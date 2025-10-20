# 🧠 Online Mechanic AI

**AI-powered automotive assistant** — upload photos or describe your car issue, and get instant diagnostic help from an AI trained on mechanical reasoning.

Built with **Python (AWS Lambda)** + **React (Frontend)** + **AWS Cloud Infrastructure** + **OpenAI GPT-4o Vision API**.

---

## 🚗 Features

- Upload photos or short videos of car issues
- Describe the problem (noise, warning light, etc.)
- AI analyses both **image + text** using GPT-4o
- Returns possible causes, safety checks, and fixes
- Hosted on AWS (S3 + Lambda + API Gateway + CloudFront)
- Simple `Makefile` automation for local testing & cloud deployment

---

## 🏗️ Architecture

```
React Frontend ─▶ AWS API Gateway ─▶ AWS Lambda (Python)
                         │
                         ├─▶ AWS S3 (store uploaded photos)
                         ├─▶ OpenAI GPT-4o Vision API
                         └─▶ DynamoDB (optional: chat history)
```

---

## 🗂️ Folder Structure

```
online-mechanic-ai/
│
├── backend/
│   ├── lambda_function.py
│   ├── requirements.txt
│   ├── Makefile
│   ├── .env.example
│   ├── scripts/set_openai_key.py
│   └── utils/s3_helper.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── Makefile
│   └── .env.example
│
├── Makefile
├── .gitignore
└── README.md
```

---

## ⚙️ Prerequisites

- Python ≥ 3.12
- Node ≥ 20
- AWS CLI configured (`aws configure`)
- OpenAI API key (from [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys))
- AWS IAM role for Lambda with `S3FullAccess` + `LambdaFullAccess`

---

## 🔑 Environment Variables

### Backend (.env or Lambda environment)

```
OPENAI_API_KEY=<your_openai_api_key>
S3_BUCKET=mechanic-ai-uploads
```

### Frontend (.env)

```
VITE_API_URL=https://your-api-gateway-url
```

---

## 🧩 Adding the OpenAI Key Securely to AWS

### 🪄 Option 1 – via Makefile (recommended)

In the root of the project:

```bash
make set-key KEY=<your_api_key>
```

This target runs:

```makefile
set-key:
@echo "🔐 Updating OpenAI key..."
aws lambda update-function-configuration \
  --function-name mechanic-ai-lambda \
  --environment "Variables={OPENAI_API_KEY=$(KEY)}"
```

---

### 🪄 Creating the project S3 bucket

Before uploading photos you need a private S3 bucket. Use the helper target to
spin one up (it defaults to `us-east-1`, pass `REGION` if you prefer another):

```bash
make create-bucket BUCKET=mechanic-ai-uploads REGION=us-west-2
```

Under the hood this runs `backend/scripts/create_s3_bucket.py`, which safely
skips creation if the bucket already exists and lets you override the canned
ACL with `ACL=public-read` or similar when needed.

---

### 🪄 Option 2 – Custom Script

`backend/scripts/set_openai_key.py`

```python
import boto3, sys
key = sys.argv[1]
lambda_name = "mechanic-ai-lambda"
client = boto3.client("lambda")

client.update_function_configuration(
    FunctionName=lambda_name,
    Environment={"Variables": {"OPENAI_API_KEY": key}}
)
print("✅ OpenAI key updated successfully in AWS Lambda.")
```

Run it:

```bash
python backend/scripts/set_openai_key.py sk-xxxxxx
```

---

## 🧰 Local Development

### 🔹 Backend (Python)

```bash
cd backend
cp .env.example .env  # update with your secrets
make run
```

Starts a local Lambda simulation using your API key (reads `.env`).

### 🔹 Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Runs React app locally on [http://localhost:3000](http://localhost:3000).

---

## 🚀 Deployment Workflow

### 1️⃣ Build Backend

```bash
make backend
```

### 2️⃣ Deploy to AWS

```bash
make deploy
```

→ Builds Lambda zip and deploys using AWS CLI.

### 3️⃣ Deploy Frontend

```bash
cd frontend && npm run deploy
```

→ Syncs `dist/` to your S3 static site bucket (update the deploy script to your needs).

---

## 🧱 Makefile Overview

### Root Makefile

```makefile
.PHONY: backend frontend deploy set-key clean

backend:
cd backend && make build

frontend:
cd frontend && npm run build

deploy:
cd backend && make deploy
cd frontend && npm run deploy

set-key:
@echo "🔐 Updating OpenAI key..."
aws lambda update-function-configuration \
  --function-name mechanic-ai-lambda \
  --environment "Variables={OPENAI_API_KEY=$(KEY)}"

clean:
cd backend && make clean
cd frontend && npm run clean
```

---

## 🧠 Example Interaction

**User:**

> The car makes a rattling noise when idling.

**AI Mechanic:**

> Possible causes: loose heat shield, worn timing chain, or low oil pressure.
> Check: oil level, exhaust brackets.
> Severity: Moderate — drive short distance only, visit workshop soon.

---

## 🔒 Security Notes

- API keys **never stored client-side**.
- Lambda environment variable holds your OpenAI key securely.
- S3 bucket restricted to `private` uploads by Lambda only.
- Optional: Use AWS Secrets Manager instead of plain environment vars.

---

## 🌐 Future Enhancements

| Feature           | Description                                  |
| ----------------- | -------------------------------------------- |
| 🧾 Cost Estimator | AI suggests approximate repair cost          |
| 📹 Video Upload   | Short clip support (≤ 10 MB)                 |
| 🗣️ Voice Input   | Use Amazon Transcribe for speech description |
| 📈 Chat History   | Store previous diagnostics in DynamoDB       |
| 🚙 VIN Decoder    | Detect car model automatically               |

---

## 📜 License

MIT License © 2025
