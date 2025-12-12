/**
 * 주에한번은 - Main Application
 * 부모님과의 대화를 더 깊게
 */

// Constants
const DAYS_KO = ['일', '월', '화', '수', '목', '금', '토'];
const CATEGORY_LABELS = { past: '과거', present: '현재', future: '미래' };
const DIFFICULTY_LABELS = { 1: '가벼움', 2: '중간', 3: '깊음' };

// State - encapsulated object instead of separate variables
const state = {
  questions: [],
  currentQuestion: null,
  weekQuestions: [],
  isLoading: false,
  error: null
};

// DOM Elements (cached on init)
let elements = {};

// Initialize application
async function init() {
  cacheElements();
  updateTodayDate();
  await loadQuestions();
  displayTodayQuestion();
  displayWeekQuestions();
  setupEventListeners();
}

// Cache DOM elements for performance
function cacheElements() {
  elements = {
    todayDate: document.getElementById('todayDate'),
    questionText: document.getElementById('questionText'),
    questionMeta: document.getElementById('questionMeta'),
    categoryTag: document.getElementById('categoryTag'),
    difficultyTag: document.getElementById('difficultyTag'),
    weekList: document.getElementById('weekList'),
    weekCount: document.getElementById('weekCount'),
    copyBtn: document.getElementById('copyBtn'),
    refreshBtn: document.getElementById('refreshBtn'),
    toast: document.getElementById('toast'),
    errorToast: document.getElementById('errorToast')
  };
}

// Update state helper
function updateState(updates) {
  Object.assign(state, updates);
}

// Load questions from JSON
async function loadQuestions() {
  updateState({ isLoading: true, error: null });

  try {
    const response = await fetch('./data/questions.json');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    updateState({ questions: data.questions, isLoading: false });
  } catch (error) {
    console.error('Failed to load questions:', error);
    updateState({
      questions: getEmbeddedQuestions(),
      isLoading: false,
      error: error.message
    });
    showError('질문을 불러오는데 실패했어요. 기본 질문을 표시합니다.');
  }
}

// Fallback embedded questions
function getEmbeddedQuestions() {
  return [
    { id: 23, text: "요즘 가장 맛있게 먹은 음식은 뭐야?", category: "present", difficulty: 1 },
    { id: 24, text: "요즘 하루 중 가장 좋은 시간은 언제야?", category: "present", difficulty: 1 },
    { id: 1, text: "내가 어렸을 때 가장 웃겼던 순간은 뭐야?", category: "past", difficulty: 1 }
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

// Get question for a specific date (deterministic based on date)
function getQuestionForDate(date) {
  if (state.questions.length === 0) return null;

  const startDate = new Date('2024-12-12');
  const diffDays = Math.floor((date - startDate) / (1000 * 60 * 60 * 24));
  const index = ((diffDays % state.questions.length) + state.questions.length) % state.questions.length;
  return state.questions[index];
}

// Display today's question
function displayTodayQuestion() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const question = getQuestionForDate(today);
  updateState({ currentQuestion: question });

  if (question) {
    elements.questionText.textContent = `"${question.text}"`;
    elements.categoryTag.textContent = CATEGORY_LABELS[question.category];
    elements.difficultyTag.textContent = DIFFICULTY_LABELS[question.difficulty];
  } else {
    elements.questionText.textContent = '질문을 불러올 수 없습니다.';
  }
}

// Display a random different question
function displayRandomQuestion() {
  const currentId = state.currentQuestion?.id;
  const filteredQuestions = state.questions.filter(q => q.id !== currentId);

  if (filteredQuestions.length === 0) return;

  const randomIndex = Math.floor(Math.random() * filteredQuestions.length);
  const question = filteredQuestions[randomIndex];
  updateState({ currentQuestion: question });

  elements.questionText.style.opacity = '0';
  setTimeout(() => {
    elements.questionText.textContent = `"${question.text}"`;
    elements.categoryTag.textContent = CATEGORY_LABELS[question.category];
    elements.difficultyTag.textContent = DIFFICULTY_LABELS[question.difficulty];
    elements.questionText.style.opacity = '1';
  }, 150);
}

// Display this week's questions
function displayWeekQuestions() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Get Monday of current week
  const monday = new Date(today);
  const dayOfWeek = today.getDay();
  const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  monday.setDate(today.getDate() + diff);

  const weekQuestions = [];
  let html = '';
  let passedCount = 0;

  for (let i = 0; i < 7; i++) {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);

    const question = getQuestionForDate(date);
    const isToday = date.getTime() === today.getTime();
    const isPast = date < today;
    const isFuture = date > today;

    let statusClass = '';
    if (isToday) statusClass = 'today';
    else if (isPast) { statusClass = 'past'; passedCount++; }
    else statusClass = 'future';

    const dayName = DAYS_KO[date.getDay()];
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;

    weekQuestions.push({ date, question, isToday });

    html += `
      <li class="week-item ${statusClass}" data-index="${i}">
        <span class="week-item-dot"></span>
        <div class="week-item-content">
          <span class="week-item-day">${dayName} ${dateStr}</span>
          <p class="week-item-text">${isFuture ? '(예정)' : (question?.text || '-')}</p>
        </div>
      </li>
    `;
  }

  updateState({ weekQuestions });
  elements.weekList.innerHTML = html;
  elements.weekCount.textContent = `${passedCount + (today >= monday ? 1 : 0)}/7`;

  // Add click handlers using event delegation
  elements.weekList.addEventListener('click', handleWeekItemClick);
}

// Handle week item click (event delegation)
function handleWeekItemClick(event) {
  const weekItem = event.target.closest('.week-item:not(.future)');
  if (!weekItem) return;

  const index = parseInt(weekItem.dataset.index);
  const { question } = state.weekQuestions[index];

  if (!question) return;

  updateState({ currentQuestion: question });

  elements.questionText.style.opacity = '0';
  setTimeout(() => {
    elements.questionText.textContent = `"${question.text}"`;
    elements.categoryTag.textContent = CATEGORY_LABELS[question.category];
    elements.difficultyTag.textContent = DIFFICULTY_LABELS[question.difficulty];
    elements.questionText.style.opacity = '1';
  }, 150);

  // Scroll to question card
  document.querySelector('.question-card').scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });
}

// Copy question to clipboard
async function copyQuestion() {
  if (!state.currentQuestion) return;

  try {
    await navigator.clipboard.writeText(state.currentQuestion.text);
    elements.copyBtn.classList.add('btn-copied');
    showToast('질문이 복사되었어요!');
    setTimeout(() => elements.copyBtn.classList.remove('btn-copied'), 300);
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = state.currentQuestion.text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('질문이 복사되었어요!');
    } catch (copyError) {
      showError('복사에 실패했어요. 직접 선택해서 복사해주세요.');
    }
    document.body.removeChild(textArea);
  }
}

// Show toast notification
function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.remove('error');
  elements.toast.classList.add('show');
  setTimeout(() => elements.toast.classList.remove('show'), 2500);
}

// Show error notification
function showError(message) {
  if (elements.errorToast) {
    elements.errorToast.textContent = message;
    elements.errorToast.classList.add('show');
    setTimeout(() => elements.errorToast.classList.remove('show'), 5000);
  } else {
    // Fallback to regular toast with error class
    elements.toast.textContent = message;
    elements.toast.classList.add('error', 'show');
    setTimeout(() => {
      elements.toast.classList.remove('show', 'error');
    }, 5000);
  }
}

// Setup event listeners
function setupEventListeners() {
  elements.copyBtn.addEventListener('click', copyQuestion);
  elements.refreshBtn.addEventListener('click', displayRandomQuestion);
}

// Start application
init();
