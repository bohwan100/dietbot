/**
 * 집밥봇 30일 식단 설계 구글 폼 원클릭 자동 생성 스크립트 (Google Apps Script)
 * 
 * [사용 방법]:
 * 1. 브라우저에서 https://script.google.com 접속 (구글 로그인)
 * 2. [+ 새 프로젝트] 클릭
 * 3. 기본 내용을 지우고 아래 코드를 그대로 붙여넣기
 * 4. 상단 [▷ 실행] 버튼 클릭 (권한 승인 팝업 시 '고급 -> 이동' 클릭)
 * 5. 실행 완료 후 하단 [실행 로그]에 생성된 구글 폼 URL(Published URL)이 즉시 출력됩니다!
 */

function createZipbabIntakeForm() {
  // 1. 구글 폼 생성
  var form = FormApp.create('30일 식단 설계 조건');
  form.setDescription('1인 자취생을 위한 퇴근 후 맛있는 저녁 한 끼(30일 일반식 플랜)를 기본값으로 설정했습니다. 구성 인원(1인)과 식사 기준(퇴근 후 저녁 30끼) 및 일반식 콘셉트는 1인 자취생에게 최적화되어 자동 설계되며, 아래 설문 조건을 자유롭게 변경하여 맞춤 신청할 수 있습니다.');
  form.setIsSpreadsheetResponse(true);

  // 1. 성함 (또는 닉네임)
  var item0 = form.addTextItem();
  item0.setTitle('1. 성함 (또는 닉네임)')
       .setHelpText('맞춤 포털 및 장바구니에 표기될 성함입니다.')
       .setRequired(true);

  // 2. 한 달 식비 예산 (원)
  var item1 = form.addTextItem();
  item1.setTitle('2. 한 달 식비 예산 (원)')
       .setHelpText('원하시는 한 달 식비 예산을 숫자로 입력해 주세요. (예: 200000 / 300000)')
       .setRequired(true);

  // 3. 선호하는 음식 취향 (복수 선택 가능)
  var item5 = form.addCheckboxItem();
  item5.setTitle('3. 선호하는 음식 취향 (복수 선택 가능)')
       .setChoiceValues([
         '한식',
         '일식',
         '양식',
         '중식'
       ])
       .setRequired(true);

  // 4. 알레르기 및 제외 식품
  var item6 = form.addTextItem();
  item6.setTitle('4. 알레르기 및 제외 식품')
       .setHelpText('없을 경우 "없음" 입력 (예: 오이, 갑각류, 견과류 등)')
       .setRequired(false);

  // 5. 집에 있는 식재료
  var item7 = form.addTextItem();
  item7.setTitle('5. 집에 있는 식재료')
       .setHelpText('없을 경우 "아무것도 없음" 입력 (예: 쌀, 간장, 고추장, 참기름 등)\n※ 이 정보가 빠지면 식단이나 구매량이 크게 달라질 수 있습니다.')
       .setRequired(false);

  // 6. 기대하는 변화 및 목표
  var item8 = form.addParagraphTextItem();
  item8.setTitle('6. 집밥봇을 통해 어떤 도움을 받고 싶고, 앞으로 어떻게 변화하고 싶으신가요?')
       .setHelpText('예: 매일 시켜 먹는 배달 음식을 끊고 식비를 절약하고 싶어요 / 퇴근 후 간편하고 건강한 집밥을 직접 챙겨 먹는 건강한 자취생이 되고 싶어요.')
       .setRequired(false);

  Logger.log('====================================================');
  Logger.log('🎉 구글 폼이 성공적으로 생성되었습니다!');
  Logger.log('고객 전달용 응답 링크: ' + form.getPublishedUrl());
  Logger.log('관리자 편집 링크: ' + form.getEditUrl());
  Logger.log('====================================================');
}
