/**
 * 집밥보이 개인 맞춤 영양 계산 엔진 (최종 개편 버전)
 * - 5단계 간편 설문 기반
 * - 결정론적 수식 & 안전 가드레일
 */

const SURVEY_CONFIG = {
  // 3-2. TDEE 활동계수 기본값 및 보정값
  activityBase: {
    sedentary: 1.20, // 대부분 앉아서 생활
    light: 1.35,     // 서 있거나 가볍게 움직임
    active: 1.50     // 육체활동이 많은 생활
  },

  exerciseBoost: {
    none: 0.0,       // 운동 없음
    '1-2': 0.08,     // 주 1~2회
    '3-4': 0.18,     // 주 3~4회
    '5+': 0.28       // 주 5회 이상
  },

  maxActivityFactor: 1.85, // 최대 활동계수 상한선

  // 3-4. 목표 칼로리 기본 비율
  goalMultipliers: {
    fat_loss: 0.85,  // 체지방 감량 기본 (TDEE × 0.85)
    maintain: 1.00,  // 체중 유지 (TDEE × 1.00)
    muscle_gain: 1.05 // 근육 증가 기본 (TDEE × 1.05)
  },

  // 3-5. 단백질 계수 (g / kg)
  proteinFactors: {
    maintain: {
      none: 1.0,     // 운동 없음
      cardio: 1.2,   // 유산소 위주
      strength: 1.4  // 근력운동 포함
    },
    fat_loss: {
      none: 1.2,     // 운동 없음
      cardio: 1.4,   // 유산소 위주
      strength: 1.8  // 근력운동 포함
    },
    muscle_gain: {
      strength: 1.8, // 근력운동 포함
      none: 1.2,     // 근력운동 없음 (임시 참고값)
      cardio: 1.2    // 유산소 위주 (임시 참고값)
    }
  },

  // 3-6. 지방 기본 비율 (% of target calories)
  fatRatio: 0.25, // 25%

  // 비만 기준 (BMI 30 이상 단백질 보정 기준체중용 BMI)
  obeseBmiThreshold: 30.0,
  referenceBmi: 25.0
};

/**
 * 2. STEP 5. 안전 확인 및 가드레일 평가
 */
function evaluateSafetyRisks(input) {
  const risks = [];
  const age = Number(input.age);
  const height = Number(input.heightCm);
  const weight = Number(input.weightKg);
  const bmi = weight / Math.pow(height / 100, 2);

  // 1. 만 19세 미만 청소년
  if (age < 19) {
    risks.push({
      type: 'underage',
      title: '성장기 청소년 영양 안내',
      message: '만 19세 미만 청소년은 신체 성장과 건강을 위해 일반 성인용 자동 감량 처방 대상에서 제외됩니다. 균형 잡힌 규칙적인 식사와 전문 영양 상담을 권장합니다.'
    });
  }

  // 2. BMI 18.5 미만 저체중 상태의 감량
  if (bmi < 18.5 && input.goal === 'fat_loss') {
    risks.push({
      type: 'underweight_loss',
      title: '저체중 상태 감량 제한',
      message: `현재 BMI는 ${bmi.toFixed(1)}로 저체중 기준(18.5 미만)입니다. 추가적인 체중 감량은 건강에 무리를 줄 수 있어 자동 감량 설계를 제공하지 않습니다. 체중 유지 또는 회복을 위한 전문가 상담을 추천합니다.`
    });
  }

  // 3. 건강 스크리닝 (STEP 5)
  const screening = input.healthScreening || 'none';
  if (screening === 'medication_illness') {
    risks.push({
      type: 'medication_illness',
      title: '건강 관리 질환 및 복용 약 안내',
      message: '질환 치료나 복용 중인 약물이 있는 경우 영양소(특히 단백질, 나트륨, 전해질)의 정밀한 조절이 필요합니다. 임의의 식단 처방 대신 담당 주치의와 상의하세요.'
    });
  } else if (screening === 'pregnancy') {
    risks.push({
      type: 'pregnancy',
      title: '임신 또는 수유 중 영양 설계',
      message: '임신·수유 중에는 모체와 아이의 건강을 위한 특수 열량 공급이 필수적입니다. 인위적인 칼로리 적자 감량 식단을 피하시고 담당 산부인과 전문의와 상담해 주세요.'
    });
  } else if (screening === 'eating_disorder') {
    risks.push({
      type: 'eating_disorder',
      title: '섭식 관련 건강 주의 안내',
      message: '섭식 관련 심리적 어려움이나 강박이 있는 경우 엄격한 칼로리 계산이 부담을 줄 수 있습니다. 수치보다는 편안한 식사와 전문가의 심리·영양 케어를 우선 권장합니다.'
    });
  } else if (screening === 'unsure') {
    risks.push({
      type: 'unsure',
      title: '전문가 영양 상담 권장',
      message: '현재 건강 상태가 불확실한 경우 표준 자동 계산 수치를 그대로 적용하기보다, 전문가의 세심한 건강 평가 후 식단을 시작하는 것이 안전합니다.'
    });
  }

  return risks;
}

/**
 * 3. 메인 결정론적 영양 계산 알고리즘
 */
function calculateDietPlan(input) {
  const age = Number(input.age);
  const height = Number(input.heightCm);
  const weight = Number(input.weightKg);
  const goal = input.goal || 'fat_loss';
  const sex = input.sexForEquation || 'male';

  // 3-3. BMI 계산
  const bmi = weight / Math.pow(height / 100, 2);

  // 3-1. RMR 계산 (Mifflin-St Jeor 식)
  // 남성: 10*W + 6.25*H - 5*A + 5
  // 여성: 10*W + 6.25*H - 5*A - 161
  const baseRmr = (10 * weight) + (6.25 * height) - (5 * age);
  const rmrMale = Math.round(baseRmr + 5);
  const rmrFemale = Math.round(baseRmr - 161);

  let rmr = 0;
  let isRange = false;
  let rmrRange = null;

  if (sex === 'male') {
    rmr = rmrMale;
  } else if (sex === 'female') {
    rmr = rmrFemale;
  } else {
    // 선택하기 어려운 경우: 임의 추정 대신 남녀 공식 둘 다 계산하여 추정 범위로 제공
    isRange = true;
    rmrRange = { min: rmrFemale, max: rmrMale };
    // 계산 진행용 대푯값(중간값)
    rmr = Math.round((rmrMale + rmrFemale) / 2);
  }

  // 3-2. TDEE 계산
  const actBase = SURVEY_CONFIG.activityBase[input.dailyActivity] || 1.20;
  const exBoost = SURVEY_CONFIG.exerciseBoost[input.exerciseFrequency] || 0.0;
  let activityFactor = actBase + exBoost;
  if (activityFactor > SURVEY_CONFIG.maxActivityFactor) {
    activityFactor = SURVEY_CONFIG.maxActivityFactor;
  }
  activityFactor = Math.round(activityFactor * 1000) / 1000;

  const tdeeExact = rmr * activityFactor;
  const tdee = Math.round(tdeeExact);

  let tdeeRange = null;
  if (isRange && rmrRange) {
    tdeeRange = {
      min: Math.round(rmrRange.min * activityFactor),
      max: Math.round(rmrRange.max * activityFactor)
    };
  }

  // 3-4. 목표 칼로리 계산 및 안전 보정
  let multiplier = SURVEY_CONFIG.goalMultipliers[goal] || 1.00;
  let safetyNotice = null;

  if (goal === 'fat_loss') {
    if (bmi < 18.5) {
      safetyNotice = '저체중 상태로 일반 감량 열량 제한을 적용하지 않습니다.';
      multiplier = 1.00;
    } else if (bmi < 20.0) {
      safetyNotice = '체중이 낮은 편이어서 무리한 감량 대신 유지 칼로리를 권장합니다.';
      multiplier = 1.00;
    } else if (bmi < 23.0) {
      // BMI 20~23 미만: 초기 TDEE × 0.90으로 완화
      multiplier = 0.90;
      safetyNotice = '정상 체중 구간으로 근손실 없는 완만한 감량(TDEE의 90%)을 적용했습니다.';
    } else {
      // BMI 23 이상: 기본 TDEE × 0.85
      multiplier = 0.85;
    }
  } else if (goal === 'muscle_gain') {
    const hasStrength = Boolean(input.includesResistanceTraining);
    if (!hasStrength) {
      // 근력운동을 하지 않으면서 근육 증가를 선택한 경우: 잉여 칼로리 부여 유보
      multiplier = 1.00;
      safetyNotice = '근력운동 없이 열량만 늘리면 체지방 위주로 증가합니다. 근성장을 위해 주 2~3회 근력운동 병행을 권장합니다.';
    } else {
      multiplier = 1.05;
    }
  }

  const rawTargetCal = tdeeExact * multiplier;
  // 50kcal 단위 반올림
  const targetCalories = Math.round(rawTargetCal / 50) * 50;

  let targetCalRange = null;
  if (isRange && tdeeRange) {
    targetCalRange = {
      min: Math.round((tdeeRange.min * multiplier) / 50) * 50,
      max: Math.round((tdeeRange.max * multiplier) / 50) * 50
    };
  }

  // 3-5. 단백질 계산
  // 운동 유형 분류: none(운동없음), cardio(유산소), strength(근력포함)
  let exType = 'none';
  if (input.exerciseFrequency && input.exerciseFrequency !== 'none') {
    exType = input.includesResistanceTraining ? 'strength' : 'cardio';
  }

  let proteinFactor = SURVEY_CONFIG.proteinFactors[goal]?.[exType] || 1.2;

  // 고도비만(BMI >= 30)의 경우 과도한 단백질 방지를 위한 기준체중 보정
  let calcWeight = weight;
  let weightAdjusted = false;
  if (bmi >= SURVEY_CONFIG.obeseBmiThreshold) {
    calcWeight = Math.round(SURVEY_CONFIG.referenceBmi * Math.pow(height / 100, 2));
    weightAdjusted = true;
    safetyNotice = (safetyNotice ? safetyNotice + ' ' : '') + `비만 구간으로 신장 부담을 방지하기 위해 기준 체중(${calcWeight}kg)으로 단백질을 산출했습니다.`;
  }

  let proteinG = Math.round(calcWeight * proteinFactor);
  let proteinCal = proteinG * 4;

  // 3-6. 지방 계산 (목표 칼로리의 25%, 0.5g 단위 반올림)
  let rawFatG = (targetCalories * SURVEY_CONFIG.fatRatio) / 9;
  let fatG = Math.round(rawFatG * 2) / 2;
  let fatCal = Math.round(fatG * 9);

  // 3-7. 탄수화물 계산 (남은 칼로리 전부 배분)
  let remainingCal = targetCalories - proteinCal - fatCal;
  let carbsG = Math.round(remainingCal / 4);

  // 3-8. 열량 일치 미세 조정 (4kcal 이내)
  let totalMacroCal = (proteinG * 4) + Math.round(fatG * 9) + (carbsG * 4);
  let calDiff = targetCalories - totalMacroCal;
  if (calDiff !== 0) {
    carbsG += Math.round(calDiff / 4);
    totalMacroCal = (proteinG * 4) + Math.round(fatG * 9) + (carbsG * 4);
    calDiff = targetCalories - totalMacroCal;
  }

  let carbsCal = carbsG * 4;

  // 퍼센트 계산
  const pctP = Math.round((proteinCal / targetCalories) * 100);
  const pctF = Math.round((fatCal / targetCalories) * 100);
  const pctC = 100 - pctP - pctF;

  return {
    goal: goal,
    age: age,
    heightCm: height,
    weightKg: weight,
    sexForEquation: sex,
    bmi: Number(bmi.toFixed(1)),
    weightAdjusted: weightAdjusted,
    calcWeightKg: calcWeight,
    dailyActivity: input.dailyActivity,
    exerciseFrequency: input.exerciseFrequency,
    includesResistanceTraining: Boolean(input.includesResistanceTraining),
    activityFactor: activityFactor,
    isRange: isRange,
    rmrKcal: rmr,
    rmrRange: rmrRange,
    tdeeKcal: tdee,
    tdeeRange: tdeeRange,
    targetCalories: targetCalories,
    targetCalRange: targetCalRange,
    proteinG: proteinG,
    proteinCal: proteinCal,
    proteinFactor: proteinFactor,
    fatG: fatG,
    fatCal: fatCal,
    fatRatio: SURVEY_CONFIG.fatRatio,
    carbsG: carbsG,
    carbsCal: carbsCal,
    macroRatioPct: { carbs: pctC, protein: pctP, fat: pctF },
    caloricDiff: calDiff,
    safetyNotice: safetyNotice,
    isIllustrative: false
  };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SURVEY_CONFIG,
    evaluateSafetyRisks,
    calculateDietPlan
  };
}
