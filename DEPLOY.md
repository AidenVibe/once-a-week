# 배포 가이드

## 웹사이트 (GitHub Pages)

### 1. GitHub 저장소 생성
```bash
cd "c:/Users/btsoft/Desktop/주에한번은"
git init
git add .
git commit -m "Initial commit: 주에한번은 MVP"
```

### 2. GitHub에 저장소 생성 후 푸시
```bash
git remote add origin https://github.com/AidenVibe/once-a-week.git
git branch -M main
git push -u origin main
```

### 3. GitHub Pages 설정
1. GitHub 저장소 → Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `main` / `/web` 폴더 선택
4. Save

### 4. 접속 URL
- `https://AidenVibe.github.io/once-a-week/`

---

## 텔레그램 봇

### 로컬 실행
```bash
cd bot
pip install -r requirements.txt
python main.py
```

### Railway 배포 (추천)
1. [Railway](https://railway.app) 가입
2. New Project → Deploy from GitHub repo
3. bot 폴더 선택
4. Environment Variables에 BOT_TOKEN 추가 (선택사항)
5. Deploy

### 또는 서버에서 실행
```bash
# 백그라운드 실행
nohup python main.py > bot.log 2>&1 &

# 로그 확인
tail -f bot.log

# 프로세스 확인/종료
ps aux | grep main.py
kill <PID>
```

---

## 봇 명령어 설정 (BotFather)

텔레그램에서 @BotFather에게 다음 명령 전송:

```
/setcommands
```

봇 선택 후:
```
start - 구독 시작하기
question - 오늘의 질문 받기
week - 이번 주 질문 보기
stop - 구독 취소
help - 도움말
```

---

## 체크리스트

- [ ] GitHub 저장소 생성
- [ ] web 폴더 GitHub Pages 배포
- [ ] 텔레그램 봇 로컬 테스트
- [ ] BotFather에서 명령어 설정
- [ ] 봇 배포 (Railway 또는 서버)
- [ ] 웹사이트에서 텔레그램 링크 동작 확인
