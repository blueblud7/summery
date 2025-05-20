// 채널 관련 함수
async function loadChannels() {
    try {
        const response = await fetch('/api/v1/youtube/channels/');
        const channels = await response.json();
        
        const channelList = document.getElementById('channelList');
        channelList.innerHTML = '';
        
        channels.forEach(channel => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <h3>${channel.title}</h3>
                <p>채널 ID: ${channel.channel_id}</p>
                <p>${channel.description || '설명 없음'}</p>
                <div class="actions">
                    <button onclick="getChannelVideos('${channel.channel_id}')">영상 보기</button>
                    <button onclick="deleteChannel('${channel.channel_id}')">삭제</button>
                </div>
            `;
            channelList.appendChild(item);
        });
    } catch (error) {
        console.error('채널 목록 로드 중 오류:', error);
        showMessage('채널 목록을 불러오는 데 실패했습니다.', 'error');
    }
}

async function addChannel() {
    const channelId = document.getElementById('channelId').value.trim();
    if (!channelId) {
        showMessage('채널 ID를 입력해주세요.', 'error');
        return;
    }
    
    try {
        // 입력값을 그대로 서버로 전송
        const response = await fetch('/api/v1/youtube/channels/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                channel_id: channelId,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '채널 추가 실패');
        }
        
        const result = await response.json();
        showMessage(`채널 "${result.title}"이(가) 추가되었습니다.`, 'success');
        document.getElementById('channelId').value = '';
        loadChannels();
    } catch (error) {
        console.error('채널 추가 중 오류:', error);
        showMessage(error.message || '채널 추가에 실패했습니다.', 'error');
    }
}

async function deleteChannel(channelId) {
    if (!confirm('이 채널을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/youtube/channels/${channelId}`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '채널 삭제 실패');
        }
        
        showMessage('채널이 삭제되었습니다.', 'success');
        loadChannels();
    } catch (error) {
        console.error('채널 삭제 중 오류:', error);
        showMessage(error.message || '채널 삭제에 실패했습니다.', 'error');
    }
}

async function getChannelVideos(channelId) {
    try {
        const response = await fetch(`/api/v1/youtube/search/by-channel/${channelId}`);
        const videos = await response.json();
        
        displayVideos(videos);
    } catch (error) {
        console.error('채널 영상 로드 중 오류:', error);
        showMessage('채널 영상을 불러오는 데 실패했습니다.', 'error');
    }
}

// 키워드 관련 함수
async function loadKeywords() {
    try {
        const response = await fetch('/api/v1/youtube/keywords/');
        const keywords = await response.json();
        
        const keywordList = document.getElementById('keywordList');
        keywordList.innerHTML = '';
        
        keywords.forEach(keyword => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <h3>${keyword.keyword}</h3>
                <p>${keyword.description || '설명 없음'}</p>
                <div class="actions">
                    <button onclick="getKeywordVideos('${keyword.keyword}')">영상 보기</button>
                    <button onclick="deleteKeyword(${keyword.id})">삭제</button>
                </div>
            `;
            keywordList.appendChild(item);
        });
    } catch (error) {
        console.error('키워드 목록 로드 중 오류:', error);
        showMessage('키워드 목록을 불러오는 데 실패했습니다.', 'error');
    }
}

async function addKeyword() {
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) {
        showMessage('키워드를 입력해주세요.', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/youtube/keywords/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '키워드 추가 실패');
        }
        
        const result = await response.json();
        showMessage(`키워드 "${result.keyword}"이(가) 추가되었습니다.`, 'success');
        document.getElementById('keyword').value = '';
        loadKeywords();
    } catch (error) {
        console.error('키워드 추가 중 오류:', error);
        showMessage(error.message || '키워드 추가에 실패했습니다.', 'error');
    }
}

async function deleteKeyword(keywordId) {
    if (!confirm('이 키워드를 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/youtube/keywords/${keywordId}`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '키워드 삭제 실패');
        }
        
        showMessage('키워드가 삭제되었습니다.', 'success');
        loadKeywords();
    } catch (error) {
        console.error('키워드 삭제 중 오류:', error);
        showMessage(error.message || '키워드 삭제에 실패했습니다.', 'error');
    }
}

async function getKeywordVideos(keyword) {
    try {
        const response = await fetch(`/api/v1/youtube/search/by-keyword/${keyword}`);
        const videos = await response.json();
        
        displayVideos(videos);
    } catch (error) {
        console.error('키워드 영상 로드 중 오류:', error);
        showMessage('키워드 영상을 불러오는 데 실패했습니다.', 'error');
    }
}

// 영상 표시 함수
function displayVideos(videos) {
    const videoContainer = document.getElementById('videoResults');
    videoContainer.innerHTML = '';
    
    if (videos.length === 0) {
        videoContainer.innerHTML = '<p class="no-results">검색 결과가 없습니다.</p>';
        return;
    }
    
    videos.forEach(video => {
        const videoItem = document.createElement('div');
        videoItem.className = 'video-item';
        videoItem.innerHTML = `
            <h3>${video.title}</h3>
            <p>${video.description ? video.description.substring(0, 100) + '...' : '설명 없음'}</p>
            <div class="video-actions">
                <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank">
                    <button>유튜브에서 보기</button>
                </a>
                <button onclick="summarizeVideo('${video.video_id}')">요약하기</button>
            </div>
        `;
        videoContainer.appendChild(videoItem);
    });
}

// 영상 요약 함수
async function summarizeVideo(videoId) {
    try {
        const response = await fetch('/api/v1/summarize/youtube', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: `https://www.youtube.com/watch?v=${videoId}`,
                language: 'ko'
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '영상 요약 실패');
        }
        
        const result = await response.json();
        
        // 요약 결과 표시
        const summaryContainer = document.getElementById('summaryResult');
        summaryContainer.innerHTML = `
            <h2>${result.title}</h2>
            <p><strong>채널:</strong> ${result.channel}</p>
            <div class="summary-content">
                <h3>요약</h3>
                <p>${result.summary}</p>
            </div>
        `;
        
        // 요약 결과로 스크롤
        summaryContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('영상 요약 중 오류:', error);
        showMessage(error.message || '영상 요약에 실패했습니다.', 'error');
    }
}

// 유틸리티 함수
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('message');
    messageContainer.textContent = message;
    messageContainer.className = `message ${type}`;
    messageContainer.style.display = 'block';
    
    setTimeout(() => {
        messageContainer.style.display = 'none';
    }, 5000);
}

// 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    // URL 쿼리 파라미터에 따라 적절한 탭 표시
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    
    if (tab === 'channels') {
        switchTab('channels');
        loadChannels();
    } else if (tab === 'keywords') {
        switchTab('keywords');
        loadKeywords();
    } else if (tab === 'search') {
        // 검색 관련 초기화 코드 (필요한 경우)
    } else {
        // 기본 탭 (manage 페이지, 쿼리 파라미터 없을 때)
        loadChannels();
        loadKeywords();
    }
    
    // 폼 제출 이벤트 연결
    document.getElementById('addChannelForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addChannel();
    });
    
    document.getElementById('addKeywordForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addKeyword();
    });
}); 