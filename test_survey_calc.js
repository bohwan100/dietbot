const { calculateDietPlan, evaluateSafetyRisks } = require('./js/survey_calculator.js');

let passed = 0;
let total = 0;

function assert(desc, condition) {
  total++;
  if (condition) {
    passed++;
    console.log(`✅ [PASS] ${desc}`);
  } else {
    console.error(`❌ [FAIL] ${desc}`);
  }
}

console.log("=== 집밥보이 5단계 최종 개편 영양 계산 엔진 테스트 시작 ===\n");

// 1. RMR 계산식 검증 (남성 vs 여성)
// 나이 30세, 키 175cm, 체중 75kg
// 남성: 10*75 + 6.25*175 - 5*30 + 5 = 750 + 1093.75 - 150 + 5 = 1698.75 -> 1699
// 여성: 10*75 + 6.25*175 - 5*30 - 161 = 750 + 1093.75 - 150 - 161 = 1532.75 -> 1533
const mTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'male', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: 'none' });
const fTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'female', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: 'none' });
assert("남성 RMR 1699 kcal 검증", mTest.rmrKcal === 1699);
assert("여성 RMR 1533 kcal 검증", fTest.rmrKcal === 1533);

// 2. 선택하기 어려움 선택 시 남녀 추정 범위 제공 검증
const neutralTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'neutral', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: 'none' });
assert("성별 선택 어려움 시 isRange 플래그 활성화", neutralTest.isRange === true);
assert("RMR 범위 min/max 제공 (1533 ~ 1699 kcal)", neutralTest.rmrRange.min === 1533 && neutralTest.rmrRange.max === 1699);

// 3. TDEE 활동계수 계산 검증 (기본 + 운동 보정)
// 좌식(1.20) + 주 3~4회(+0.18) = 1.38
const actTest1 = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'male', goal: 'maintain', dailyActivity: 'sedentary', exerciseFrequency: '3-4' });
assert("좌식 + 주 3~4회 활동계수 1.38", actTest1.activityFactor === 1.38);

// 육체노동(1.50) + 주 5회이상(+0.28) = 1.78
const actTest2 = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'male', goal: 'maintain', dailyActivity: 'active', exerciseFrequency: '5+' });
assert("육체노동 + 주 5회이상 활동계수 1.78", actTest2.activityFactor === 1.78);

// 4. 목표별 칼로리 및 안전 보정 (BMI 기준 감량율)
// BMI 24.5 (175cm, 75kg) -> BMI >= 23 이므로 기본 0.85 적용
// TDEE = 1699 * 1.38 = 2344.62 -> 2344.62 * 0.85 = 1992.9 -> 50단위 반올림: 2000 kcal
const lossTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: 'male', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: '3-4', includesResistanceTraining: true });
assert("감량 목표 50kcal 반올림 (2000 kcal)", lossTest.targetCalories === 2000);

// BMI 21.0 (175cm, 64.3kg) -> BMI 20~23 미만이므로 0.90 완화 적용
const mildLossTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 64.3, sexForEquation: 'male', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: 'none' });
assert("BMI 20~23 정상 체중 구간 감량율 0.90 완화 적용", mildLossTest.safetyNotice && mildLossTest.safetyNotice.includes('90%'));

// 5. 단백질 계산 로직 검증 (감량 + 근력운동 = 체중 × 1.8g)
// 75kg * 1.8 = 135g
assert("감량 + 근력운동 포함 시 단백질 체중 × 1.8g (135g)", lossTest.proteinG === 135);

// 6. 지방 계산 검증 (2000kcal의 25% = 500kcal / 9 = 55.5g)
assert("지방 25% 0.5g 단위 계산 (55.5g)", lossTest.fatG === 55.5);

// 7. 탄수화물 계산 및 열량 총합 검증 (오차 4kcal 이내)
// 목표 2000kcal - 단백질 540kcal - 지방 500kcal = 960kcal -> 탄수화물 240g
// 총 열량: 135*4 + 500 + 240*4 = 540 + 500 + 960 = 2000kcal
assert("탄수화물 계산 (240g)", lossTest.carbsG === 240);
const totalSum = (lossTest.proteinG * 4) + lossTest.fatCal + (lossTest.carbsG * 4);
const diff = Math.abs(lossTest.targetCalories - totalSum);
assert(`열량 총합과 목표 칼로리 오차 4kcal 이내 (실제 오차: ${diff}kcal)`, diff <= 4);

// 8. 고도비만(BMI >= 30) 단백질 기준체중 보정 검증
// 175cm, 105kg (BMI = 34.3) -> 기준 체중 BMI 25 = 25 * 1.75^2 = 76.56 -> 77kg
const obeseTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 105, sexForEquation: 'male', goal: 'fat_loss', dailyActivity: 'sedentary', exerciseFrequency: 'none' });
assert("BMI 30 이상 단백질 기준체중 보정 적용 (77kg 기준)", obeseTest.weightAdjusted === true && obeseTest.calcWeightKg === 77);

// 9. 안전 확인 스크리닝 (STEP 5) 검증
const safe1 = evaluateSafetyRisks({ age: 17, heightCm: 170, weightKg: 65, goal: 'fat_loss', healthScreening: 'none' });
assert("만 19세 미만 감량 제외 검출", safe1.some(r => r.type === 'underage'));

const safe2 = evaluateSafetyRisks({ age: 25, heightCm: 170, weightKg: 48, goal: 'fat_loss', healthScreening: 'none' }); // BMI 16.6
assert("저체중 감량 제한 검출", safe2.some(r => r.type === 'underweight_loss'));

const safe3 = evaluateSafetyRisks({ age: 28, heightCm: 165, weightKg: 58, goal: 'fat_loss', healthScreening: 'medication_illness' });
assert("건강 문제/복용 약 스크리닝 시 전문가 상담 분기 검출", safe3.some(r => r.type === 'medication_illness'));


// 10. 활동계수 상한 1.85 캡 검증
const maxActTest = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 75, sexForEquation: "male", goal: "maintain", dailyActivity: "active", exerciseFrequency: "5+" });
assert("활동계수 최대 1.85 이하 유지 검증", maxActTest.activityFactor <= 1.85);

// 11. 유지 목표 단백질 계수 검증 (운동 없음 1.0, 유산소 1.2, 근력 1.4)
const mNone = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 70, sexForEquation: "male", goal: "maintain", dailyActivity: "sedentary", exerciseFrequency: "none" });
assert("유지 + 운동없음 단백질 체중 × 1.0g (70g)", mNone.proteinG === 70);

const mCardio = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 70, sexForEquation: "male", goal: "maintain", dailyActivity: "sedentary", exerciseFrequency: "3-4", includesResistanceTraining: false });
assert("유지 + 유산소 단백질 체중 × 1.2g (84g)", mCardio.proteinG === 84);

const mStrength = calculateDietPlan({ age: 30, heightCm: 175, weightKg: 70, sexForEquation: "male", goal: "maintain", dailyActivity: "sedentary", exerciseFrequency: "3-4", includesResistanceTraining: true });
assert("유지 + 근력 단백질 체중 × 1.4g (98g)", mStrength.proteinG === 98);

// 12. 근육 증가(muscle_gain) 검증
// 근력 포함 시 TDEE × 1.05 & 단백질 1.8g
const gainStrength = calculateDietPlan({ age: 25, heightCm: 180, weightKg: 70, sexForEquation: "male", goal: "muscle_gain", dailyActivity: "light", exerciseFrequency: "3-4", includesResistanceTraining: true });
assert("근육증가 + 근력포함 시 단백질 체중 × 1.8g (126g)", gainStrength.proteinG === 126);

// 근력 미포함 시 열량 흑자 보류(multiplier 1.00) 및 안내
const gainNoStrength = calculateDietPlan({ age: 25, heightCm: 180, weightKg: 70, sexForEquation: "male", goal: "muscle_gain", dailyActivity: "light", exerciseFrequency: "none" });
assert("근육증가 + 근력미포함 시 열량 흑자 유보 및 권장 안내", gainNoStrength.safetyNotice && gainNoStrength.safetyNotice.includes("근력운동"));

console.log(`\n=== 테스트 완료: ${passed} / ${total} 통과 ===`);
if (passed === total) {
  process.exit(0);
} else {
  process.exit(1);
}
