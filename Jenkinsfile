node {
  stage('Init') {
    checkout scm
  }
    
  stage('Build & Test') {
    try {
      sh 'docker-compose -f docker-compose.tests.yml -p hotmaps up --build --exit-code-from excess_heat_cm'
    }
    finally {
      // stop services
      sh 'docker-compose -f docker-compose.tests.yml down -v --rmi all --remove-orphans' 
    }
  }
    // get commit id
  env.COMMIT_ID = sh(returnStdout: true, script: 'git rev-parse HEAD')
  env.REPO_NAME = getRepoName()

  stage('Deploy') {
    echo "Deploying commit $COMMIT_ID of repository $REPO_NAME on branch $BRANCH_NAME"
    if (env.BRANCH_NAME == 'develop') {
      echo "Deploying to DEV platform"
      sshagent(['sshhotmapsdev']) {
        sh 'ssh -o StrictHostKeyChecking=no -l iig hotmapsdev.hevs.ch "/var/hotmaps/deploy_cm.sh \$REPO_NAME \$COMMIT_ID"'
      }
    } else if (env.BRANCH_NAME == 'master') {
      echo "Deploying to PROD platform"
       sshagent(['sshhotmapsdev']) {
        sh 'ssh -o StrictHostKeyChecking=no -l iig hotmaps.hevs.ch "/var/hotmaps/deploy_cm.sh \$REPO_NAME \$COMMIT_ID"'
      }
    } else {
      echo "${env.BRANCH_NAME}: not deploying"
    }
  }
}

String getRepoName() {
    return scm.getUserRemoteConfigs()[0].getUrl().tokenize('/').last().split("\\.")[0]
}
