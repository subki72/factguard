# 🛡️ CekFakta: AI Fake News & Political Bias Detector

<div align="center">
  <img src="https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/Groq-Llama_3-f55036?style=for-the-badge" alt="Groq Llama 3" />
</div>
<br/>

**CekFakta** adalah platform cerdas berbasis *Artificial Intelligence* (Generative AI) yang dirancang untuk membongkar narasi manipulatif, mendeteksi indikasi *buzzer*, dan mengukur tingkat objektivitas sebuah teks, artikel berita, maupun *screenshot* media sosial. Dibangun dengan antarmuka bergaya **Neo-Brutalism** yang berani dan modern.

## Fitur Utama

- **Analisis Berbasis AI (Groq + Llama 3):** Membedah teks untuk mencari logical fallacy, bias politik, dan sentimen emosional dengan kecepatan kilat.
- **Optical Character Recognition (OCR):** Tidak hanya teks dan URL, AI mampu membaca teks langsung dari tangkapan layar (screenshot) media sosial atau berita.
- **Smart Web Scraping:** Otomatis mengekstrak teks utama dari URL berita Indonesia untuk dianalisis.
- **Sistem Skor & Transparansi:** Memberikan skor objektivitas (0-100) dan penjelasan poin-per-poin (*reasoning*) mengapa sebuah narasi dianggap bias atau manipulatif.
- **Sistem Komunitas (Vote & Diskusi):** Pengguna yang *login* dapat memberikan *vote* (Setuju/Tidak Setuju) dan berdiskusi pada hasil analisis.
- **Neo-Brutalism UI:** Desain antarmuka yang tegas, berani, tanpa kompromi—mencerminkan perlawanan terhadap misinformasi.

## Tech Stack

- **Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS v4, Lucide React
- **Backend:** FastAPI (Python), httpx, BeautifulSoup4
- **Database & Auth:** Supabase (PostgreSQL + Google OAuth)
- **AI Inference:** Groq API (Llama-3-70b-8192)
- **Deployment:** Vercel (Serverless Functions)

## Instalasi & Menjalankan di Lokal (Local Development)

### 1. Persiapan Kebutuhan (Prerequisites)
- [Node.js](https://nodejs.org/) (Versi 18+ direkomendasikan)
- [Python](https://www.python.org/) (Versi 3.9+)
- Akun [Supabase](https://supabase.com/) & [Groq Cloud](https://console.groq.com/)

### 2. Clone Repository
```bash
git clone https://github.com/USERNAME_ANDA/factguard.git
cd factguard
```

### 3. Instalasi Dependencies
Aplikasi ini berjalan sebagai Monorepo (Next.js dan FastAPI berada di direktori yang sama untuk Vercel Serverless).
```bash
# Instal dependency frontend (Node)
npm install

# Instal dependency backend (Python)
pip install -r api/requirements.txt
```

### 4. Konfigurasi Environment Variables
Buat file `.env` di *root directory* proyek, dan isi dengan variabel berikut:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

GROQ_API_KEY=your_groq_api_key

# Untuk pengembangan lokal
NEXT_PUBLIC_API_URL=http://localhost:8000

# Konfigurasi SMTP (Opsional, untuk fitur Kritik & Saran)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=email_anda@gmail.com
SMTP_PASSWORD=password_aplikasi_gmail
```

### 5. Menjalankan Aplikasi
Karena frontend (Next.js) dan backend (FastAPI) berjalan di *port* terpisah saat mode pengembangan, Anda perlu membuka **dua terminal**.

**Terminal 1 (Backend - FastAPI):**
```bash
uvicorn api.main:app --reload --port 8000
```
Backend berjalan di `http://localhost:8000`.

**Terminal 2 (Frontend - Next.js):**
```bash
npm run dev
```
Buka `http://localhost:3000` di browser Anda!


