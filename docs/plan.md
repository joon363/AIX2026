너는 하드웨어 아키텍처 전문가야. 현재 Pre-trained Yolo model을 FPGA에 올리기 위해 양자화를 수행할 거야. 


# Darknet(YOLO) INT8 양자화(Quantization) 파이프라인 구축 계획서

## 1. 프로젝트 배경 및 환경 제약

본 프로젝트는 기존 32-bit 부동소수점(FP32)으로 학습된 YOLO 모델을 엣지/하드웨어 디바이스에 올리기 위해 8-bit 정수(INT8)로 양자화하는 과정(Post-Training Quantization, PTQ)을 최적화하는 것을 목표로 합니다.
main.c가 접근점이며 yolov2_forward_network는 32비트로 실행, yolov2_forward_network_quantized는 양자화 파라미터를 사용해 8비트로 실행합니다.
이때 backward pass는 없으며 _quantized 파일의 양자화 파라미터를 바꾸고 양자화 방식을 조정해 최적의 결과를 내는 것이 목표입니다.

**[핵심 환경 제약 사항]**

1. **`main.c` 수정 불가:** 프로그램의 제어 흐름을 바꿀 수 없습니다. 이미지가 로드되기도 전에 `do_quantization` 함수가 먼저 호출되는 구조를 그대로 수용해야 합니다.
2. 수정할 수 있는 파일: 
3. **Backward Pass 부재:** 역전파 로직이 없으므로 QAT(Quantization-Aware Training)는 불가능합니다.
4. **디스크 I/O 병목 제한:** 400MB 원본 텐서를 파일로 쓰는 것은 불가능합니다.

## 2. 접근 방식의 변천사 (History)

- **초기안 (Python 기반 원본 덤프):** I/O 병목 및 자동화 적용의 어려움으로 기각.
- **대안 1 (고정 범위 히스토그램 누적):** `MAX_RANGE`를 20.0f 등으로 하드코딩할 경우, 레이어 및 이미지별로 달라지는 실제 값의 분포를 제대로 담아낼 수 없어 정확도가 떨어지는 문제 발견.
- **대안 2 (파일 무한 Append):** 100장의 캘리브레이션 이미지를 돌릴 때, 텍스트 파일 하나에 모든 히스토그램을 계속 누적(Append)하면 파일 관리가 불가능해지는 문제 발견.

## 3. 최종 솔루션: "동적 범위(Dynamic Range) 히스토그램 및 EMA 기반 Online PTQ"

하드코딩된 범위를 버리고 **사진마다, 레이어마다 실제 최댓값(Max)을 기반으로 동적 히스토그램을 생성**합니다. 생성된 히스토그램에서 즉시 최적의 Threshold를 계산하고, 여러 장의 사진 통계는 **지수 이동 평균(EMA, Exponential Moving Average)**으로 부드럽게 누적하여, 단 몇 줄짜리 최종 Multiplier 텍스트 파일만 깔끔하게 갱신(Overwrite)합니다.

모든 주요 변수는 Grid Search가 가능하도록 매크로(`define`)로 상단에 분리합니다.

## 4. 단계별 구현 계획 (Action Plan)

### Step 1: `yolov2_forward_network.c` 수정 (동적 캘리브레이션 및 EMA 누적)

`forward_convolutional_layer_cpu` 함수 상단에 매크로를 정의하고, 연산 직전에 동적으로 Percentile 기반 Multiplier를 계산하여 EMA로 누적한 뒤, 파일에 **덮어쓰기(`w`)**로 저장합니다.

```
// === Grid Search를 위한 하이퍼파라미터 매크로 정의 ===
#define CALIB_NUM_BINS 2048       // 히스토그램 구간 수
#define CALIB_PERCENTILE 0.999f   // Percentile 기준 (예: 상위 0.1% 무시)
#define CALIB_EMA_ALPHA 0.1f      // EMA 가중치 (100장 기준, 최신값 10% 반영)
#define QUANT_MAX_VAL 127.0f      // INT8 최대값

// forward_convolutional_layer_cpu 연산(gemm_nn) 직전 추가

// 1. 현재 사진 & 레이어에 맞는 동적 Max 구하기
float current_max = 0.000001f;
for (int i = 0; i < l.inputs; i++) {
    float val = fabs(state.input[i]);
    if (val > current_max) current_max = val;
}

// 2. 현재 사진 전용 로컬 히스토그램 생성
int local_hist[CALIB_NUM_BINS] = {0};
for (int i = 0; i < l.inputs; i++) {
    float val = fabs(state.input[i]);
    int bin = (int)((val / current_max) * (CALIB_NUM_BINS - 1));
    local_hist[bin]++;
}

// 3. 현재 사진의 Percentile Threshold 계산
long long target = (long long)(l.inputs * CALIB_PERCENTILE);
long long cumulative = 0;
float optimal_threshold = current_max;

for (int b = 0; b < CALIB_NUM_BINS; b++) {
    cumulative += local_hist[b];
    if (cumulative >= target) {
        // 구간 인덱스를 다시 실수 값으로 복원
        optimal_threshold = ((float)b / (CALIB_NUM_BINS - 1)) * current_max;
        break;
    }
}
if (optimal_threshold <= 0.0001f) optimal_threshold = 0.0001f;
float current_multiplier = QUANT_MAX_VAL / optimal_threshold;

// 4. 여러 사진에 대한 통계를 EMA(지수 이동 평균)로 누적
static float ema_multipliers[200] = {0}; // 레이어별 누적 Multiplier 보관용
if (ema_multipliers[state.index] == 0.0f) {
    ema_multipliers[state.index] = current_multiplier; // 첫 번째 사진의 값
} else {
    ema_multipliers[state.index] = (CALIB_EMA_ALPHA * current_multiplier) +
                                   ((1.0f - CALIB_EMA_ALPHA) * ema_multipliers[state.index]);
}

// 5. 최종 통계만 깔끔하게 파일에 덮어쓰기("w" 모드)
// 사진을 100장 돌려도 파일 사이즈는 항상 동일하며, 최적화된 Multiplier 값만 담김
FILE *fp = fopen("calibration_multipliers.txt", "w");
if (fp) {
    for (int i = 0; i < net.n; i++) {
        if (ema_multipliers[i] > 0) {
            fprintf(fp, "%d %f\n", i, ema_multipliers[i]); // "레이어인덱스 Multiplier" 형식
        }
    }
    fclose(fp);
}
```

### Step 2: `yolov2_forward_network_quantized.c` 수정 (최종 양자화 적용)

추론 모드로 실행될 때, `do_quantization` 함수는 무거운 연산 없이 위에서 만들어진 작고 깔끔한 `calibration_multipliers.txt` 파일만 읽어 양자화를 수행합니다.

```
// do_quantization 함수 내부 재작성

FILE *fp = fopen("calibration_multipliers.txt", "r");
if (!fp) {
    printf("[오류] calibration_multipliers.txt 파일이 없습니다. 캘리브레이션을 먼저 진행하세요.\n");
    return;
}

// 파일에서 Multiplier 미리 읽어서 배열에 저장
float loaded_multipliers[200] = {0};
int l_idx;
float l_mult;
while (fscanf(fp, "%d %f", &l_idx, &l_mult) != EOF) {
    loaded_multipliers[l_idx] = l_mult;
}
fclose(fp);

for (j = 0; j < net.n; ++j) {
    layer *l = &net.layers[j];

    if (l->type == CONVOLUTIONAL) {
        size_t const filter_size = l->size * l->size * l->c;
        int i, fil;

        // 1. 파일에서 읽어온 EMA Multiplier 적용 (입력/Activation 양자화)
        l->input_quant_multiplier = (loaded_multipliers[j] > 0) ? loaded_multipliers[j] : 16.0f;

        // 2. Weight Multiplier 계산 (가중치는 고정이므로 여기서 바로 MinMax 연산 수행)
        float max_w = 0.000001f;
        for (i = 0; i < l->size * l->size * l->c * l->n; ++i) {
            float val = fabs(l->weights[i]);
            if (val > max_w) max_w = val;
        }
        l->weights_quant_multiplier = 127.0f / max_w;

        // 3. Weight 및 Bias 양자화 실행 (기존 로직과 동일)
        // ... (Scale & Clip 반복문) ...

        printf(" CONV%d: \tInput %g \tWeight %g\n", j, l->input_quant_multiplier, l->weights_quant_multiplier);
    }
}
```

## 5. 기대 효과 및 향후 연구(Grid Search) 방향

1. **완벽한 동적 스케일링 (Dynamic Scaling):** 이제 각 레이어와 사진마다 최댓값이 달라져도, 해당 사진에 맞는 100% 최적화된 히스토그램을 매번 새로 그려냅니다.
2. **단일 파일 & 용량 문제 해결:** 100장의 캘리브레이션 이미지를 돌려도 `calibration_multipliers.txt` 파일 하나에 최종 스케일 값(EMA)만 덮어씌워지므로 빠르고 깔끔합니다.
3. **Grid Search 편의성:** C 코드 최상단에 정의된 `#define` 매크로 3개(`CALIB_PERCENTILE`, `CALIB_NUM_BINS`, `CALIB_EMA_ALPHA`)의 숫자만 바꾸며 실험을 돌리면 가장 mAP가 높게 나오는 최적의 조합을 손쉽게 찾을 수 있습니다.

## 6. 자동 테스트 및 실행
1. /app에서 make clean && make -j
2. cd bin
3. ./script-unix-aix2024-test-all.sh (모든 이미지를 돌리면서 하나의 multipliers 파일 생성, 45초 소요)
4. ./script-unix-aix2024-test-all-quantized.sh (실행, 120초 소요)
5. 실행하면 마지막에  mean average precision (mAP) = 0.550382, or 55.04 % 이렇게 나와.
위 과정을 여러 파라미터에 대해 실행해 보고 최적의 조합을 찾아내는 파이썬 파일이나 배시 스크립트를 작성해줘. 시간이 꽤 걸리는 작업이기 때문에 적절한 파라미터 조합으로 20종류정도만 해줘. 중간중간 계속 best 결과값을 best_params.txt에 저장해둬