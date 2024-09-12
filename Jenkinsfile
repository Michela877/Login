pipeline {
    agent any

    stages {
        stage('Clone repository') {
            steps {
                git branch: 'master', url: 'https://github.com/Michela877/Login.git'
            }
        }
        
        stage('Install dependencies') {
            steps {
                script {
                    powershell '''
                        $pythonLauncherPath = "C:\\Users\\admin-corso\\AppData\\Local\\Programs\\Python\\Launcher\\py.exe"
                        & $pythonLauncherPath -m venv venv
                        .\\venv\\Scripts\\Activate.ps1
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    powershell '''
                        if (docker images -q login) {
                            docker rm login
                        }
                        docker build -t login:latest .
                    '''
                    
                }
            }
        }

        stage('Run Docker container') {
            steps {
                script {
                    powershell '''
                        if (docker ps -q --filter "name=login_container") {
                            docker stop login_container
                        }
                        if (docker ps -aq --filter "name=login_container") {
                            docker rm login_container
                        }
                        docker run -d -p 13000:13000 --name login_container login:latest
                    '''
                }
            }
        }
        
        stage('Remove Docker images') {
            steps {
                script {
                    powershell '''
                        if (docker images -f "dangling=true" -q) {
                            docker image prune -f
                        }
                    ''' 
                }                
            }
        }
    }
}
