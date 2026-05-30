const questions = window.GAME_QUESTIONS || [];
const secondsPerQuestion = window.SECONDS_PER_QUESTION || 30;
const character = window.PLAYER_CHARACTER || "Knight";
let index = 0, crystal = 0, correct = 0, timeLeft = secondsPerQuestion, timer = null, shieldUsed = false;
const qNo = document.getElementById('questionNo');
const qText = document.getElementById('questionText');
const choices = document.getElementById('choices');
const timerText = document.getElementById('timerText');
const timerBar = document.getElementById('timerBar');
const progressFill = document.getElementById('progressFill');
const crystalText = document.getElementById('crystalText');
const feedback = document.getElementById('feedback');
function crystalFromTime(t){ if(t>=25) return 10; if(t>=20) return 8; if(t>=10) return 5; if(t>0) return 3; return 0; }
function showQuestion(){
  if(index >= questions.length){ finishGame(); return; }
  const q = questions[index];
  qNo.textContent = index + 1;
  qText.textContent = q.question;
  progressFill.style.width = `${(index/questions.length)*100}%`;
  feedback.textContent = '';
  feedback.className = 'feedback';
  choices.innerHTML = '';
  q.choices.forEach(c => {
    const btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'choice-btn'; btn.textContent = c;
    btn.onclick = () => answer(c);
    choices.appendChild(btn);
  });
  timeLeft = secondsPerQuestion;
  updateTimer();
  clearInterval(timer);
  timer = setInterval(() => { timeLeft--; updateTimer(); if(timeLeft <= 0){ answer(null); } }, 1000);
}
function updateTimer(){
  timerText.textContent = Math.max(timeLeft,0);
  timerBar.style.width = `${Math.max(timeLeft,0)/secondsPerQuestion*100}%`;
}
function lockChoices(){ document.querySelectorAll('.choice-btn').forEach(b => b.disabled = true); }
function answer(choice){
  clearInterval(timer); lockChoices();
  const q = questions[index];
  if(choice === q.answer){
    let gain = crystalFromTime(timeLeft);
    if(character === 'Archer' && timeLeft >= secondsPerQuestion - 5) gain += 2;
    crystal += gain; correct += 1;
    feedback.textContent = `ถูกต้อง! ได้รับ ${gain} Crystal 💎`;
    feedback.className = 'feedback good';
  } else {
    if(character === 'Priest' && !shieldUsed && choice !== null){
      shieldUsed = true;
      feedback.textContent = `Priest Shield ช่วยไว้! คำตอบที่ถูกคือ ${q.answer}`;
      feedback.className = 'feedback good';
    } else {
      feedback.textContent = `ยังไม่ถูก คำตอบคือ ${q.answer}`;
      feedback.className = 'feedback bad';
    }
  }
  crystalText.textContent = crystal;
  index++;
  setTimeout(showQuestion, 1200);
}
function finishGame(){
  progressFill.style.width = '100%';
  document.getElementById('crystalInput').value = crystal;
  document.getElementById('correctInput').value = correct;
  document.getElementById('submitForm').submit();
}
showQuestion();
