# before AP (첫 번째 결과)
before = {
0:82.37,1:73.66,2:94.83,3:79.07,4:94.44,5:100.00,6:100.00,7:90.18,
8:95.57,9:97.04,10:89.13,11:100.00,12:79.70,13:100.00,14:57.00,
15:85.88,16:69.00,17:34.13,18:78.91,19:73.27,20:64.75,21:100.00,
22:84.46,23:90.72,24:100.00,25:73.53,26:90.05,27:91.21,28:77.93,
29:61.59,30:57.76,31:74.59,32:60.20,33:11.17,34:41.16,35:97.71,
36:86.78,37:100.00,38:87.18,39:85.22,40:66.87,41:85.76,42:94.20,
43:99.47,44:91.53,45:64.94,46:89.97,47:92.30,48:96.27,49:81.82,
50:100.00,51:94.65,52:79.72,53:74.48,54:88.93,55:95.94,56:44.72,
57:86.10,58:81.61,59:85.90
}

# after AP (두 번째 결과)
after = {
0:65.62,1:6.01,2:68.77,3:39.48,4:37.74,5:46.83,6:91.80,7:61.93,
8:55.42,9:95.20,10:93.21,11:78.82,12:70.80,13:76.66,14:16.34,
15:61.87,16:53.42,17:19.31,18:37.42,19:55.15,20:44.29,21:78.57,
22:69.65,23:19.91,24:86.33,25:59.90,26:79.30,27:72.69,28:28.81,
29:39.93,30:23.59,31:21.31,32:35.52,33:9.09,34:28.92,35:57.37,
36:84.12,37:87.30,38:69.79,39:32.63,40:61.68,41:89.12,42:73.35,
43:45.40,44:80.00,45:35.23,46:72.98,47:24.98,48:87.83,49:59.94,
50:98.99,51:66.98,52:32.10,53:22.91,54:58.06,55:71.00,56:10.08,
57:47.84,58:65.94,59:37.09
}

import matplotlib.pyplot as plt

# class id 정렬 (안전하게 맞추기)
class_ids = sorted(before.keys())

before_vals = [before[cid] for cid in class_ids]
after_vals  = [after[cid]  for cid in class_ids]

x = list(range(len(class_ids)))
width = 0.35

x_before = [i - width/2 for i in x]
x_after  = [i + width/2 for i in x]

plt.figure(figsize=(18, 6))
plt.bar(x_before, before_vals, width=width, label='Before')
plt.bar(x_after,  after_vals,  width=width, label='After')

plt.xlabel('class_id')
plt.ylabel('AP (%)')
plt.title('AP Comparison (Before vs After)')
plt.xticks(x, class_ids)
plt.legend()

plt.tight_layout()
plt.savefig("ap_comparison.png", dpi=300, bbox_inches="tight")
plt.close()

# class_id → name 매핑
names = {
0:"aunt_jemima_original_syrup",1:"band_aid_clear_strips",
2:"bumblebee_albacore",3:"cholula_chipotle_hot_sauce",
4:"crayola_24_crayons",5:"hersheys_cocoa",
6:"honey_bunches_of_oats_honey_roasted",
7:"honey_bunches_of_oats_with_almonds",
8:"hunts_sauce",9:"listerine_green",10:"mahatma_rice",
11:"white_rain_body_wash",12:"pringles_bbq",13:"cheeze_it",
14:"hersheys_bar",15:"redbull",
16:"mom_to_mom_sweet_potato_corn_apple",
17:"a1_steak_sauce",18:"jif_creamy_peanut_butter",
19:"cinnamon_toast_crunch",20:"arm_hammer_baking_soda",
21:"dr_pepper",22:"haribo_gold_bears_gummi_candy",
23:"bulls_eye_bbq_sauce_original",24:"reeses_pieces",
25:"clif_crunch_peanut_butter",
26:"mom_to_mom_butternut_squash_pear",
27:"pop_tararts_strawberry",
28:"quaker_big_chewy_chocolate_chip",29:"spam",
30:"coffee_mate_french_vanilla",
31:"pepperidge_farm_milk_chocolate_macadamia_cookies",
32:"kitkat_king_size",33:"snickers",
34:"toblerone_milk_chocolate",
35:"clif_z_bar_chocolate_chip",
36:"nature_valley_crunchy_oats_n_honey",
37:"ritz_crackers",38:"palmolive_orange",
39:"crystal_hot_sauce",40:"tapatio_hot_sauce",
41:"nabisco_nilla_wafers",
42:"pepperidge_farm_milano_cookies_double_chocolate",
43:"campbells_chicken_noodle_soup",
44:"frappuccino_coffee",
45:"chewy_dips_chocolate_chip",
46:"chewy_dips_peanut_butter",
47:"nature_vally_fruit_and_nut",
48:"cheerios",
49:"lindt_excellence_cocoa_dark_chocolate",
50:"hersheys_symphony",
51:"campbells_chunky_classic_chicken_noodle",
52:"martinellis_apple_juice",
53:"dove_pink",54:"dove_white",
55:"david_sunflower_seeds",
56:"monster_energy",
57:"act_ii_butter_lovers_popcorn",
58:"coca_cola_glass_bottle",
59:"twix"
}

# 차이 계산
diff = []
for cid in before:
    delta = (before[cid] - after[cid])
    diff.append((cid, names[cid], delta))

# 정렬
diff_sorted = sorted(diff, key=lambda x: x[2], reverse=True)

print("=== 가장 차이가 큰 5개 ===")
for cid, name, delta in diff_sorted[:5]:
    print(f"{cid} ({name}) : {delta:.2f}%")

print("\n=== 가장 차이가 적은 5개 ===")
for cid, name, delta in diff_sorted[-5:]:
    print(f"{cid} ({name}) : {delta:.2f}%")

