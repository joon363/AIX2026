# YOLO 모델 Activation 분포 분석 및 양자화 전략 연구 정리

## 1. 문제 배경

YOLO 모델의 레이어별 activation 분포를 히스토그램 및 CDF 기반으로 분석하였다. 기존에는 percentile 기반 threshold(예: 0.999 ~ 0.9999)를 사용하여 클리핑 기반 스케일을 산출하였다.

실험 결과, percentile 값을 높일수록(0.998 → 0.9999) 성능이 개선되는 경향이 관찰되었다. 이는 tail 영역이 실제로 중요한 정보를 포함하고 있음을 시사한다.

---

## 2. 레이어별 분포 특성 분석

### 2.1 초기 레이어 (예: Layer 2)

- 0 근처에 매우 큰 peak 존재
- 급격히 감소하는 long-tail 구조
- 높은 sparsity (ReLU 이후 0 activation 다수)
- Heavy right-skewed distribution

해석:

- Edge/texture 중심의 저수준 특징 표현
- 일부 강한 feature에만 큰 activation 발생
- Outlier 제거 영향이 비교적 작음

---

### 2.2 후반 레이어 (예: Layer 17)

- 감소 기울기가 완만함
- tail이 두꺼움
- 값이 상대적으로 고르게 분포
- sparsity 감소

해석:

- Semantic feature 및 detection score 표현 단계
- 작은 activation 차이가 detection 결과에 직접 영향
- Tail 영역이 실제 예측에 중요

---

## 3. 핵심 인사이트

1. 레이어가 깊어질수록 activation 분포는
    - sparse + exponential decay 형태에서
    - dense + 완만한 heavy-tail 구조로 변화
2. 후반 레이어일수록 clipping에 민감
3. 높은 percentile에서 성능이 좋아진 이유:
    - tail 영역 보존
    - detection score 왜곡 감소
4. 히스토그램과 CDF의 시각적 차이는
    - 히스토그램은 절대 빈도
    - CDF는 누적 확률
    - 0 activation 비율이 높을 경우 CDF는 0에서 큰 점프 발생

---

## 4. 양자화 전략 재정립

### 4.1 기존 전략

- 모든 레이어 동일 percentile 적용

문제점:

- 후반 레이어에서 정보 손실 가능
- 구조적 특성 미반영

---

### 4.2 제안 전략 (Layer-wise Hybrid Strategy)

### 전략: 레이어 구간 분리

- Layer 0~6: percentile (0.9999 수준)
- Layer 8~17: max 기반
- Detection head: max + EMA

이유:

- 초기 레이어는 clipping 영향 작음
- 후반 레이어는 tail 보존 필수

---

## 5. 하드웨어 관점 평가

### Max 기반

- O(N) reduction
- SIMD 친화적
- 하드웨어 primitive 존재
- 구현 단순

### Histogram 기반

- bin 계산 및 random memory write 필요
- atomic 연산 필요 가능
- cache 비효율
- 구현 복잡

결론:

- 현재 분포 특성상 percentile 이득이 거의 없음
- max 기반이 하드웨어/성능 측면에서 유리

---

## 6. 구현 방향성 및 계획

### 6.1 Histogram 기반 유지 여부에 대한 결론

실험 결과 99.99% percentile은 전체 샘플 중 상위 0.01%만 제거하는 수준이며,

실제 threshold 값이 max와 거의 동일하게 수렴하는 경향을 보였다.

예:

- N = 100,000일 경우 상위 약 10개 값만 제거
- 대부분의 경우 마지막 bin 일부만 제거되는 효과

따라서 현재 YOLO 분포 특성(후반 레이어 tail 중요, clipping 민감)을 고려할 때

histogram 기반 percentile은 실질적 이득이 거의 없다.

또한 연산 관점에서:

- Max 기반: 단순 reduction, 순차 메모리 접근, SIMD/하드웨어 친화적
- Histogram 기반: bin 계산 + random memory write, 캐시 비효율, 구현 복잡도 증가

결론적으로 99.99% 수준을 사용할 경우 histogram 유지의 실익이 낮으며,

max + EMA 기반 전략이 정확도 및 하드웨어 효율 측면에서 더 합리적이다.

---

### 6.2 구현 계획

- Histogram 제거
- 전략 A 채택