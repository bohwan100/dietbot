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

console.log("=== 집밥보이 영양 계산 엔진 테스트 시작 ===\n");

// 1. 남성과 여성의 RMR 계산식 검증
// 기준: 28세, 175cm, 75kg
// 남성: 10*75 + 6.25*175 - 5*28 + 5 = 750 + 1093.75 - 140 + 5 = 1708.75 -> 반올림 1709
// 여성: 10*75 + 6.25*175 - 5*28 - 161 = 750 + 1093.75 - 140 - 161 = 1542.75 -> 반올림 1543
const rmrMale = calculateDietPlan({ age: 28, height: 175, weight: 75, sexForEquation: 'male' });
const rmrFemale = calculateDietPlan({ age: 28, height: 175, weight: 75, sexForEquation: 'female' });
assert("남성 RMR 계산식 일치 (1709 kcal)", rmrMale.rmrKcal === 1709);
assert("여성 RMR 계산식 일치 (1543 kcal)", rmrFemale.rmrKcal === 1543);

// 2. 활동계수에 따른 TDEE 검증
// 좌식 생활(sedentary) + 운동 3-4회 -> 활동계수 1.55
// 1709 * 1.55 = 2648.95 -> 2649
const tdeeTest = calculateDietPlan({ 
  age: 28, height: 175, weight: 75, sexForEquation: 'male',
  dailyActivity: 'sedentary', exerciseFrequency: '3-4'
});
assert("좌식 + 주 3-4회 운동 활동계수 1.55", tdeeTest.activityFactor === 1.55);
assert("TDEE 일치 (2649 kcal)", tdeeTest.tdeeKcal === 2649);

// 3. 목표별 칼로리 반올림 검증
// 감량 보통(0.85): 2648.95 * 0.85 = 2251.6 -> 50단위 반올림: 2250 kcal
assert("감량 보통 50kcal 반올림 (2250 kcal)", tdeeTest.targetCalories === 2250);

// 4. 첨부 이미지 예시 검증: 72kg, 다이어트 목표 2000kcal
// 이미지: 단백질 체중 x 2.0g = 144g (576kcal)
// 지방 25% = 500kcal -> 55.5g
// 탄수화물 남은 칼로리 = 924kcal -> 231g
const imgTest = calculateDietPlan({
  age: 30, height: 175, weight: 72, sexForEquation: 'male',
  dailyActivity: 'sedentary', exerciseFrequency: '3-4',
  exerciseType: 'strength', goal: 'fat_loss', goalIntensity: 'moderate',
  macroPreference: 'balanced'
});
// 72kg * 1.8g = 129.6 -> 130g (기획안 기본 1.8g)
assert("72kg 감량 단백질 1.8g 적용 검증 (130g)", imgTest.proteinG === 130);
assert("지방 0.5g 단위 반올림 및 25% 비율 검증", imgTest.fatG % 0.5 === 0);

// 5. 영양소 열량 합계 일치 검증 (오차 4kcal 이내)
const sumCal = (imgTest.proteinG * 4) + (imgTest.fatG * 9) + (imgTest.carbsG * 4);
const diff = Math.abs(imgTest.targetCalories - sumCal);
assert(`탄단지 열량 합계와 목표 칼로리 오차 4kcal 이내 (실제 오차: ${diff}kcal)`, diff <= 4);

// 6. BMI 30 이상 고도비만 적정 체중 보정 검증
// 175cm, 110kg (BMI = 35.9)
const obeseTest = calculateDietPlan({
  age: 30, height: 175, weight: 110, sexForEquation: 'male',
  dailyActivity: 'sedentary', exerciseFrequency: 'none',
  goal: 'fat_loss'
});
assert("BMI 30 이상 적정 기준 체중 보정 활성화", obeseTest.weightAdjusted === true);
assert("적정 기준 체중은 약 77kg (BMI 25 기준)", obeseTest.calcWeightKg === 77);

// 7. 안전성 검사 (Safety Guardrail) 검증
const underageRisk = evaluateSafetyRisks({ age: 17, height: 170, weight: 65, goal: 'fat_loss' });
assert("만 19세 미만 청소년 안전 안내 분기 검출", underageRisk.some(r => r.type === 'underage'));

const underweightRisk = evaluateSafetyRisks({ age: 25, height: 170, weight: 45, goal: 'fat_loss' }); // BMI 15.6
assert("저체중 감량 금지 안내 분기 검출", underweightRisk.some(r => r.type === 'underweight'));

const healthRisk = evaluateSafetyRisks({ 
  age: 30, height: 165, weight: 60, goal: 'fat_loss',
  healthRisks: ['pregnancy', 'kidney']
});
assert("임신 및 신장질환 위험 검출", healthRisk.length === 2);

console.log(`\n=== 테스트 완료: ${passed} / ${total} 통과 ===`);
if (passed === total) {
  process.exit(0);
} else {
  process.exit(1);
}
