/**
 * 주에한번은 - App v3.0 (AI Studio Inspired)
 */

// ========================================
// Constants
// ========================================
const START_DATE = new Date('2024-12-12');
START_DATE.setHours(0, 0, 0, 0);

const DAYS_KO = ['일', '월', '화', '수', '목', '금', '토'];
const THEME_LABELS = { past: '과거', future: '미래' };

const CHARACTER_MESSAGES = [
  '전화 한 통 어때요?',
  '오늘도 화이팅!',
  '부모님이 기다리셔요',
  '따뜻한 말 한마디',
  '지금이 타이밍!',
  '목소리 들려주세요'
];

// ========================================
// State
// ========================================
let dailyQuestions = [];
let specialQuestions = [];

// ========================================
// DOM Elements
// ========================================
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// ========================================
// Date Utilities
// ========================================
function getDaysSinceStart(date) {
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.floor((target - START_DATE) / (1000 * 60 * 60 * 24));
}

function formatDate(date) {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAYS_KO[date.getDay()];
  return `${month}월 ${day}일 ${dayName}요일`;
}

function formatShortDate(date) {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const dayName = DAYS_KO[date.getDay()];
  return `${dayName} ${month}/${day}`;
}

// ========================================
// Question Selection
// ========================================
function getDailyQuestion(date) {
  if (dailyQuestions.length === 0) return null;
  const days = getDaysSinceStart(date);
  const index = ((days % dailyQuestions.length) + dailyQuestions.length) % dailyQuestions.length;
  return dailyQuestions[index];
}

function getSpecialQuestion(date) {
  if (specialQuestions.length === 0) return null;
  const days = getDaysSinceStart(date);
  const index = ((days % specialQuestions.length) + specialQuestions.length) % specialQuestions.length;
  return specialQuestions[index];
}

// ========================================
// Data Loading
// ========================================
async function loadQuestions() {
  try {
    const response = await fetch('./data/questions.json');
    const data = await response.json();
    dailyQuestions = data.questions.daily || [];
    specialQuestions = data.questions.special || [];
    return true;
  } catch (error) {
    console.error('Failed to load questions:', error);
    return false;
  }
}

// ========================================
// Rendering
// ========================================
function displayTodayDate() {
  const today = new Date();
  $('#todayDate').textContent = formatDate(today);
}

function displayTodayQuestions() {
  const today = new Date();

  // Daily question
  const daily = getDailyQuestion(today);
  if (daily) {
    $('#dailyQuestionText').textContent = `"${daily.text}"`;
  }

  // Special question
  const special = getSpecialQuestion(today);
  if (special) {
    $('#specialQuestionText').textContent = `"${special.text}"`;
    const themeTag = $('#specialThemeTag');
    const themeKey = special.theme || 'past';
    themeTag.textContent = THEME_LABELS[themeKey] || themeKey;
    themeTag.className = `theme-tag ${themeKey}`;
  }
}

function displayPastQuestions() {
  const pastList = $('#pastList');
  pastList.innerHTML = '';

  const today = new Date();

  for (let i = 1; i <= 7; i++) {
    const pastDate = new Date(today);
    pastDate.setDate(today.getDate() - i);

    const daily = getDailyQuestion(pastDate);
    const special = getSpecialQuestion(pastDate);
    const dateStr = formatShortDate(pastDate);

    // Daily question item
    if (daily) {
      pastList.appendChild(createHistoryItem(dateStr, 'daily', '일상', daily.text));
    }

    // Special question item
    if (special) {
      const themeKey = special.theme || 'past';
      const themeLabel = THEME_LABELS[themeKey] || themeKey;
      pastList.appendChild(createHistoryItem(dateStr, themeKey, themeLabel, special.text));
    }
  }
}

function createHistoryItem(date, type, label, text) {
  const li = document.createElement('li');
  li.className = 'history-item';
  li.innerHTML = `
    <div class="history-item-content">
      <div class="history-item-meta">
        <span class="history-item-date">${date}</span>
        <span class="history-item-label ${type}">${label}</span>
      </div>
      <p class="history-item-text">${text}</p>
    </div>
    <div class="history-item-icon">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
    </div>
  `;
  li.addEventListener('click', () => {
    copyToClipboard(text);
    trackEvent('copy_past', { question_type: type });
  });
  return li;
}

// ========================================
// Clipboard
// ========================================
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('질문이 복사되었습니다');
    triggerCharacterHappy();
    return true;
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
      showToast('질문이 복사되었습니다');
      triggerCharacterHappy();
      document.body.removeChild(textArea);
      return true;
    } catch (copyError) {
      showToast('복사에 실패했습니다', true);
      document.body.removeChild(textArea);
      return false;
    }
  }
}

// ========================================
// Toast
// ========================================
function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.className = isError ? 'toast error show' : 'toast show';

  setTimeout(() => {
    toast.className = 'toast';
  }, 2000);
}

// ========================================
// Character Interaction
// ========================================
let characterTimeout = null;

function triggerCharacterHappy(message = '복사 완료!') {
  const character = $('#character');
  const bubbleText = $('#bubbleText');

  // Clear existing timeout
  if (characterTimeout) {
    clearTimeout(characterTimeout);
  }

  // Set message and show happy state
  bubbleText.textContent = message;
  character.classList.add('happy');

  // Reset after delay
  characterTimeout = setTimeout(() => {
    character.classList.remove('happy');
  }, 2500);
}

function setupCharacterClick() {
  const character = $('#character');

  character.addEventListener('click', () => {
    // Don't trigger if already in happy state
    if (character.classList.contains('happy')) return;

    // Pick random message
    const randomMsg = CHARACTER_MESSAGES[Math.floor(Math.random() * CHARACTER_MESSAGES.length)];
    triggerCharacterHappy(randomMsg);
  });
}

// ========================================
// Mobile Detection
// ========================================
function detectMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function hideKakaoOnDesktop() {
  if (!detectMobile()) {
    $$('.mobile-only').forEach(el => {
      el.style.display = 'none';
    });
  }
}

// ========================================
// Event Handlers
// ========================================
function setupEventListeners() {
  const today = new Date();
  const daily = getDailyQuestion(today);
  const special = getSpecialQuestion(today);

  // Copy buttons
  $('#copyDailyBtn').addEventListener('click', () => {
    if (daily) {
      copyToClipboard(daily.text);
      trackEvent('copy_daily');
    }
  });

  $('#copySpecialBtn').addEventListener('click', () => {
    if (special) {
      copyToClipboard(special.text);
      trackEvent('copy_special');
    }
  });

  // Kakao buttons
  $('#kakaoDailyBtn').addEventListener('click', () => {
    if (daily) {
      copyToClipboard(daily.text);
      trackEvent('open_kakao', { question_type: 'daily' });
    }
  });

  $('#kakaoSpecialBtn').addEventListener('click', () => {
    if (special) {
      copyToClipboard(special.text);
      trackEvent('open_kakao', { question_type: 'special' });
    }
  });

  // Character click
  setupCharacterClick();
}

// ========================================
// Analytics (GA4)
// ========================================
function trackEvent(eventName, params = {}) {
  if (typeof gtag === 'function') {
    gtag('event', eventName, params);
  }
}

// ========================================
// Initialization
// ========================================
async function init() {
  // Load questions
  const loaded = await loadQuestions();
  if (!loaded) {
    showToast('질문을 불러오는데 실패했습니다', true);
    return;
  }

  // Display content
  displayTodayDate();
  displayTodayQuestions();
  displayPastQuestions();

  // Setup
  hideKakaoOnDesktop();
  setupEventListeners();
}

// Start app
document.addEventListener('DOMContentLoaded', init);
