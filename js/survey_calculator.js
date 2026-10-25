/**
 * 집밥보이 — 나에게 맞는 식단 찾기
 * 결정론적 영양 계산 엔진 (Mifflin-St Jeor & TDEE & 탄단지 배분)
 */

const SURVEY_CONFIG = {
  // 활동계수 매트릭스 [dailyActivity][exerciseFrequency]
  activityFactors: {
    sedentary: {
      none: 1.2,
      '1-2': 1.375,
      '3-4': 1.55,
      '5+': 1.725
    },
    light: {
      none: 1.375,
      '1-2': 1.55,
      '3-4': 1.725,
      '5+': 1.9
    },
    active: {
      none: 1.725,
      '1-2': 1.9,
      '3-4': 1.9,
      '5+': 1.9
    }
  },

  // 목표별 칼로리 조정 비율
  goalMultipliers: {
    fat_loss: {
      slow: 0.90,     // 천천히
      moderate: 0.85, // 보통 (추천)
      fast: 0.80      // 빠르게
    },
    maintain: {
      default: 1.00
    },
    muscle_gain: {
      slow: 1.05,     // 체지방 최소화 천천히
      moderate: 1.08  // 보통 (추천)
    }
  },

  // 단백질 계수 (g / kg)
  proteinFactors: {
    maintain: {
      none: 1.2,
      cardio: 1.4,
      strength: 1.6,
      both: 1.6
    },
    fat_loss: {
      none: 1.4,
      cardio: 1.6,
      strength: 1.8,
      both: 1.8
    },
    muscle_gain: {
      strength: 1.8,
      both: 1.8,
      none: 1.4,   // 임시 계산값
      cardio: 1.4  // 임시 계산값
    }
  },

  // 지방 비율 (% of total calories)
  fatRatios: {
    high_carb: 0.20,  // 탄수화물 선호 20%
    balanced: 0.25,   // 균형 잡힌 식사 25% (기본/추천)
    high_fat: 0.30    // 지방 선호 30%
  },

  minFatPerKg: 0.6 // 체중 1kg당 최소 지방 g
};

/**
 * 안전성 검사 함수 (Safety Guardrail)
 */
function evaluateSafetyRisks(input) {
  const risks = [];
  const age = Number(input.age);
  const height = Number(input.height);
  const weight = Number(input.weight);
  const bmi = weight / Math.pow(height / 100, 2);

  // 1. 미성년자 (만 19세 미만)
  if (age < 19) {
    risks.push({
      type: 'underage',
      title: '청소년 성장기 특별 안내',
      message: '만 19세 미만 청소년은 신체 성장과 두뇌 발달을 위해 일반 성인용 열량 제한이나 자동 감량 처방을 적용하지 않습니다. 균형 잡힌 3끼 식사와 소아청소년 전문 영양 상담을 권장합니다.'
    });
  }

  // 2. 저체중 (BMI 18.5 미만)
  if (bmi < 18.5 && input.goal === 'fat_loss') {
    risks.push({
      type: 'underweight',
      title: '저체중 상태 감량 주의',
      message: `현재 BMI는 ${bmi.toFixed(1)}로 저체중 기준(18.5 미만)입니다. 추가적인 체지방 감량은 면역력 저하와 호르몬 불균형을 유발할 수 있으므로 체중 감량 프로그램을 제한합니다. 영양 회복 및 전문의 상담을 추천드립니다.`
    });
  }

  // 3. 건강 질환 및 특수 상태 체크
  const healthRisks = input.healthRisks || [];
  if (healthRisks.includes('pregnancy')) {
    risks.push({
      type: 'pregnancy',
      title: '임신 또는 수유 중 영양 안내',
      message: '임신 및 수유 중에는 산모와 아이의 건강을 위한 특수 열량 및 미량 영양소 공급이 최우선입니다. 인위적인 칼로리 적자 다이어트를 중단하시고 담당 산부인과 전문의와 상담해 주세요.'
    });
  }

  if (healthRisks.includes('kidney')) {
    risks.push({
      type: 'kidney',
      title: '신장 질환 등 식단 제한 질환',
      message: '신장 질환이나 만성 대사 질환이 있는 경우 단백질(질소 노폐물) 및 전해질(나트륨·칼륨·인)의 정밀한 개별 맞춤 조절이 필수적입니다. 일반 고단백 식단을 절대 그대로 적용하지 마시고 주치의의 지침을 따르세요.'
    });
  }

  if (healthRisks.includes('eating_disorder')) {
    risks.push({
      type: 'eating_disorder',
      title: '섭식 관련 심리적 안정 안내',
      message: '섭식장애 병력이나 음식에 대한 극심한 불안/강박이 있는 경우, 엄격한 칼로리 카운팅은 증상을 악화시킬 수 있습니다. 수치에 얽매이지 않고 마음과 몸의 회복을 돕는 전문가 상담을 우선적으로 권장합니다.'
    });
  }

  return risks;
}

/**
 * 결정론적 메인 영양 계산기
 */
function calculateDietPlan(input) {
  const age = Number(input.age);
  const height = Number(input.height);
  const weight = Number(input.weight);
  const bmi = weight / Math.pow(height / 100, 2);

  // 1. 휴식대사량(RMR / 편의상 BMR) 추정 (Mifflin-St Jeor 식)
  // 남성: 10*W + 6.25*H - 5*A + 5
  // 여성: 10*W + 6.25*H - 5*A - 161
  let rmr = (10 * weight) + (6.25 * height) - (5 * age);
  let sexNote = '';

  if (input.sexForEquation === 'male') {
    rmr += 5;
    sexNote = '남성 기준 공식 (+5)';
  } else if (input.sexForEquation === 'female') {
    rmr -= 161;
    sexNote = '여성 기준 공식 (-161)';
  } else {
    // 선택이 어려운 경우: 남녀 상수의 중간값 적용 (-78)
    rmr -= 78;
    sexNote = '중립 추정 공식 (남녀 중간값 적용, 약 ±83kcal 범위)';
  }

  rmr = Math.round(rmr);

  // 2. 활동계수 및 TDEE 산출
  const actDaily = input.dailyActivity || 'sedentary';
  const actFreq = input.exerciseFrequency || 'none';
  const activityFactor = SURVEY_CONFIG.activityFactors[actDaily]?.[actFreq] || 1.2;

  const tdeeExact = rmr * activityFactor;
  const tdee = Math.round(tdeeExact);

  // 3. 목표 칼로리 계산
  const goal = input.goal || 'fat_loss';
  const intensity = input.goalIntensity || (goal === 'maintain' ? 'default' : 'moderate');
  const goalMultiplier = SURVEY_CONFIG.goalMultipliers[goal]?.[intensity] || 1.0;

  let rawTargetCal = tdeeExact * goalMultiplier;
  // 실용성을 위한 50kcal 단위 반올림
  let targetCalories = Math.round(rawTargetCal / 50) * 50;

  // 4. 단백질 계산 (BMI 30 이상 적정 체중 보정 포함)
  let calcWeight = weight;
  let weightAdjusted = false;
  if (bmi >= 30) {
    // BMI 25 기준 적정 체중 산출
    calcWeight = Math.round(25 * Math.pow(height / 100, 2));
    weightAdjusted = true;
  }

  const exType = (actFreq === 'none') ? 'none' : (input.exerciseType || 'strength');
  let proteinFactor = SURVEY_CONFIG.proteinFactors[goal]?.[exType];
  if (!proteinFactor) {
    proteinFactor = (goal === 'fat_loss') ? 1.6 : (goal === 'muscle_gain' ? 1.8 : 1.4);
  }

  let proteinG = Math.round(calcWeight * proteinFactor);
  let proteinCal = proteinG * 4;

  // 5. 지방 계산 (목표 칼로리의 20%~30%, 0.5g 단위 반올림)
  const pref = input.macroPreference || 'balanced';
  const fatRatio = SURVEY_CONFIG.fatRatios[pref] || 0.25;

  let fatG = ((targetCalories * fatRatio) / 9);
  // 0.5g 단위 반올림
  fatG = Math.round(fatG * 2) / 2;

  // 체중당 최소 0.6g 보정
  const minFat = Math.round((weight * SURVEY_CONFIG.minFatPerKg) * 2) / 2;
  if (fatG < minFat) {
    fatG = minFat;
  }
  let fatCal = fatG * 9;

  // 6. 탄수화물 계산 (남은 칼로리 전부 배분)
  let remainingCal = targetCalories - proteinCal - fatCal;
  let carbsG = Math.round(remainingCal / 4);

  // 7. 반올림 후 열량 일치 미세 조정 (4kcal 이내 완벽 일치)
  let totalMacroCal = (proteinG * 4) + (fatG * 9) + (carbsG * 4);
  let calDiff = targetCalories - totalMacroCal;

  // 칼로리 차이가 있으면 탄수화물로 조정
  if (calDiff !== 0) {
    const carbAdjust = Math.round(calDiff / 4);
    carbsG += carbAdjust;
    totalMacroCal = (proteinG * 4) + (fatG * 9) + (carbsG * 4);
    calDiff = targetCalories - totalMacroCal;
  }

  // 백분율 계산
  const pctP = Math.round((proteinCal / targetCalories) * 100);
  const pctF = Math.round((fatCal / targetCalories) * 100);
  const pctC = 100 - pctP - pctF;

  return {
    goal: goal,
    age: age,
    sexForEquation: input.sexForEquation,
    sexNote: sexNote,
    heightCm: height,
    weightKg: weight,
    bmi: Number(bmi.toFixed(1)),
    weightAdjusted: weightAdjusted,
    calcWeightKg: calcWeight,
    activityFactor: activityFactor,
    dailyActivity: actDaily,
    exerciseFrequency: actFreq,
    exerciseType: exType,
    goalIntensity: intensity,
    macroPreference: pref,
    rmrKcal: rmr,
    tdeeKcal: tdee,
    targetCalories: targetCalories,
    proteinG: proteinG,
    proteinCal: proteinG * 4,
    proteinFactor: proteinFactor,
    fatG: fatG,
    fatCal: Math.round(fatG * 9),
    fatRatio: fatRatio,
    carbsG: carbsG,
    carbsCal: carbsG * 4,
    macroRatioPct: { carbs: pctC, protein: pctP, fat: pctF },
    caloricDiff: calDiff,
    isIllustrative: false
  };
}

// Node.js 환경 내보내기 지원
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SURVEY_CONFIG,
    evaluateSafetyRisks,
    calculateDietPlan
  };
}
