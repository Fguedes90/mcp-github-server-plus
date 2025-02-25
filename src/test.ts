import { githubRequest } from './common/utils.js';

async function testGitHubToken() {
    console.error('Testing GitHub token...');
    console.error('Token present:', !!process.env.GITHUB_PERSONAL_ACCESS_TOKEN);
    
    try {
        const response = await githubRequest('https://api.github.com/user');
        console.error('GitHub token is valid, user:', response);
    } catch (error) {
        console.error('GitHub token error:', error);
    }
}

testGitHubToken(); 