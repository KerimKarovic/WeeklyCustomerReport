// Jenkinsfile (place in repo root)
pipeline {
agent {
    docker {
      // Use a slim Python; no need to build your own image for this job
    image 'python:3.11-slim'
      // Speeds up pip across builds
    args '-v $HOME/.cache/pip:/root/.cache/pip:rw'
    }
}

  // Run every Monday at 06:00 Europe/Berlin (hashes minute to spread load)
  triggers { cron('H 06 * * 1') }

options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 20, unit: 'MINUTES')
}

environment {
    TZ = 'Europe/Berlin'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PYTHONDONTWRITEBYTECODE = '1'
    PYTHONUNBUFFERED = '1'
}

stages {
    stage('Checkout') {
    steps { checkout scm }
    }

    stage('System deps (if any)') {
    steps {
        sh '''
        set -eux
        apt-get update -y
        # Add system libs only if you actually need them. Most projects don't.
        # apt-get install -y --no-install-recommends fonts-dejavu
        rm -rf /var/lib/apt/lists/*
        '''
    }
    }

    stage('Install Python deps') {
    steps {
        sh '''
        set -eux
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        '''
    }
    }

    stage('Prepare .env') {
    steps {
        // Preferred: store your .env as a Jenkins "Secret file" credential (ID: weekly-report-dotenv)
        withCredentials([file(credentialsId: 'weekly-report-dotenv', variable: 'DOTENV_FILE')]) {
        sh 'cp "$DOTENV_FILE" .env'
        }
    }
    }

    stage('Generate & Send Weekly Reports') {
    steps {
        // Your entry point lives in app/main.py → run as a module
        sh '''
        set -eux
        python -m app.main
        '''
    }
    }

    stage('Archive PDFs') {
    steps {
        // Keep a copy of what was sent
        archiveArtifacts artifacts: 'output/**/*.pdf', fingerprint: true, onlyIfSuccessful: false
    }
    }
}
post {
    always {
      // A quick summary of what was produced
    sh 'echo "PDFs generated:" && ls -lah output || true'
    }
    failure {
    mail to: 'devops@yourdomain.tld',
        subject: "❌ Weekly Report job failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
        body: "See ${env.BUILD_URL}"
    }
}
}
