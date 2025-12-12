/**
 * 주에한번은 - Main Application v2.0
 * 부모님과의 대화를 더 깊게
 */

// Constants
const DAYS_KO = ['일', '월', '화', '수', '목', '금', '토'];
const THEME_LABELS = { past: '과거', future: '미래' };
const START_DATE = new Date('2024-12-12');

// State
const state = {
  dailyQuestions: [],
  specialQuestions: [],
  currentDaily: null,
  currentSpecial: null,
  pastQuestions: [],
  isLoading: false,
  isMobile: false
};

// DOM Elements
let elements = {};

// Initialize application
async function init() {
  detectMobile();
  cacheElements();
  updateTodayDate();
  await loadQuestions();
  displayTodayQuestions();
  displayPastQuestions();
  setupEventListeners();
  hideKakaoOnDesktop();
}

// Detect mobile device
function detectMobile() {
  state.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Hide Kakao buttons on desktop
function hideKakaoOnDesktop() {
  if (!state.isMobile) {
    document.querySelectorAll('.mobile-only').forEach(el => {
      el.style.display = 'none';
    });
  }
}

// Cache DOM elements
function cacheElements() {
  elements = {
    todayDate: document.getElementById('todayDate'),
    dailyQuestionText: document.getElementById('dailyQuestionText'),
    specialQuestionText: document.getElementById('specialQuestionText'),
    specialThemeTag: document.getElementById('specialThemeTag'),
    pastList: document.getElementById('pastList'),
    copyDailyBtn: document.getElementById('copyDailyBtn'),
    copySpecialBtn: document.getElementById('copySpecialBtn'),
    kakaoDailyBtn: document.getElementById('kakaoDailyBtn'),
    kakaoSpecialBtn: document.getElementById('kakaoSpecialBtn'),
    toast: document.getElementById('toast')
  };
}

// Load questions from JSON
async function loadQuestions() {
  state.isLoading = true;

  try {
    const response = await fetch('./data/questions.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    state.dailyQuestions = data.questions.daily;
    state.specialQuestions = data.questions.special;
    state.isLoading = false;
  } catch (error) {
    console.error('Failed to load questions:', error);
    state.dailyQuestions = getEmbeddedDaily();
    state.specialQuestions = getEmbeddedSpecial();
    state.isLoading = false;
    showToast('질문을 불러오는데 실패했어요.', true);
  }
}

// Fallback embedded questions
function getEmbeddedDaily() {
  return [
    { id: 1, text: "요즘 가장 맛있게 먹은 음식은 뭐야?", order: 1 },
    { id: 2, text: "요즘 하루 중 가장 좋은 시간은 언제야?", order: 2 }
  ];
}

function getEmbeddedSpecial() {
  return [
    { id: 101, text: "내가 어렸을 때 가장 웃겼던 순간은 뭐야?", theme: "past", order: 1 },
    { id: 102, text: "같이 가보고 싶은 곳 있어?", theme: "future", order: 2 }
  ];
}

// Update today's date display
function updateTodayDate() {
  const today = new Date();
  const month = today.getMonth() + 1;
  const date = today.getDate();
  const day = DAYS_KO[today.getDay()];
  elements.todayDate.textContent = `${month}월 ${date}일 ${day}요일`;
}

// Get days since start date
function getDaysSinceStart(date) {
  const targetDate = new Date(date);
  targetDate.setHours(0, 0, 0, 0);
  const diffTime = targetDate - START_DATE;
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

// Get question for a specific date (deterministic)
function getDailyQuestion(date) {
  if (state.dailyQuestions.length === 0) return null;
  const days = getDaysSinceStart(date);
  const index = ((days % state.dailyQuestions.length) + state.dailyQuestions.length) % state.dailyQuestions.length;
  return state.dailyQuestions[index];
}

function getSpecialQuestion(date) {
  if (state.specialQuestions.length === 0) return null;
  const days = getDaysSinceStart(date);
  const index = ((days % state.specialQuestions.length) + state.specialQuestions.length) % state.specialQuestions.length;
  return state.specialQuestions[index];
}

// Display today's questions
function displayTodayQuestions() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Daily question
  state.currentDaily = getDailyQuestion(today);
  if (state.currentDaily) {
    elements.dailyQuestionText.textContent = `"${state.currentDaily.text}"`;
  } else {
    elements.dailyQuestionText.textContent = '질문을 불러올 수 없습니다.';
  }

  // Special question
  state.currentSpecial = getSpecialQuestion(today);
  if (state.currentSpecial) {
    elements.specialQuestionText.textContent = `"${state.currentSpecial.text}"`;
    elements.specialThemeTag.textContent = THEME_LABELS[state.currentSpecial.theme] || '';
  } else {
    elements.specialQuestionText.textContent = '질문을 불러올 수 없습니다.';
  }
}

// Display past 7 days questions (8 days ago and older disappear)
function displayPastQuestions() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const pastQuestions = [];
  let html = '';

  // Loop through past 7 days (yesterday to 7 days ago)
  for (let i = 1; i <= 7; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);

    const daily = getDailyQuestion(date);
    const special = getSpecialQuestion(date);

    const dayName = DAYS_KO[date.getDay()];
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;

    pastQuestions.push({ date, daily, special });

    html += `
      <li class="past-item" data-index="${i - 1}">
        <div class="past-item-header">
          <span class="past-item-day">${dayName} ${dateStr}</span>
          <span class="past-item-ago">${i}일 전</span>
        </div>
        <div class="past-item-questions">
          <div class="past-question">
            <span class="past-label">일상</span>
            <p class="past-text">${daily?.text || '-'}</p>
          </div>
          <div class="past-question">
            <span class="past-label ${special?.theme || ''}">${special?.theme ? THEME_LABELS[special.theme] : '특별'}</span>
            <p class="past-text">${special?.text || '-'}</p>
          </div>
        </div>
      </li>
    `;
  }

  state.pastQuestions = pastQuestions;
  elements.pastList.innerHTML = html;

  // Add click handlers for past questions
  elements.pastList.querySelectorAll('.past-question').forEach((el) => {
    el.addEventListener('click', handlePastQuestionClick);
  });
}

// Handle past question click (copy directly)
function handlePastQuestionClick(event) {
  const textEl = event.currentTarget.querySelector('.past-text');
  if (!textEl || textEl.textContent === '-') return;

  copyToClipboard(textEl.textContent);
  trackEvent('copy_past', { question_text: textEl.textContent.substring(0, 50) });
}

// Copy question to clipboard
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('질문이 복사되었어요!');
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('질문이 복사되었어요!');
    } catch (copyError) {
      showToast('복사에 실패했어요.', true);
    }
    document.body.removeChild(textArea);
  }
}

// Copy handlers
function copyDaily() {
  if (!state.currentDaily) return;
  copyToClipboard(state.currentDaily.text);
  trackEvent('copy_daily', { question_id: state.currentDaily.id });
}

function copySpecial() {
  if (!state.currentSpecial) return;
  copyToClipboard(state.currentSpecial.text);
  trackEvent('copy_special', { question_id: state.currentSpecial.id, theme: state.currentSpecial.theme });
}

// Kakao handlers
function openKakaoDaily() {
  trackEvent('open_kakao', { type: 'daily', question_id: state.currentDaily?.id });
}

function openKakaoSpecial() {
  trackEvent('open_kakao', { type: 'special', question_id: state.currentSpecial?.id });
}

// GA4 Event Tracking
function trackEvent(eventName, params = {}) {
  if (typeof gtag === 'function') {
    gtag('event', eventName, params);
  }
}

// Show toast notification
function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.classList.toggle('error', isError);
  elements.toast.classList.add('show');
  setTimeout(() => elements.toast.classList.remove('show'), 2500);
}

// Setup event listeners
function setupEventListeners() {
  elements.copyDailyBtn.addEventListener('click', copyDaily);
  elements.copySpecialBtn.addEventListener('click', copySpecial);

  if (elements.kakaoDailyBtn) {
    elements.kakaoDailyBtn.addEventListener('click', openKakaoDaily);
  }
  if (elements.kakaoSpecialBtn) {
    elements.kakaoSpecialBtn.addEventListener('click', openKakaoSpecial);
  }
}

// Start application
init();
