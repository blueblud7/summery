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
    
    // 로딩 메시지 표시
    showMessage('채널 정보를 가져오는 중...', 'info');
    
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
        
        const result = await response.json();
        
        if (!response.ok) {
            // 자세한 오류 메시지 처리
            const errorMsg = result.detail || '채널 추가 실패';
            console.error('채널 추가 중 API 오류:', errorMsg);
            
            // 일반적인 오류 메시지 대신 더 구체적인 오류 메시지 표시
            if (errorMsg.includes('Channel not found')) {
                showMessage('채널을 찾을 수 없습니다. 정확한 채널 ID 또는 URL을 입력해주세요.', 'error');
            } else if (errorMsg.includes('이미 등록된 채널')) {
                showMessage('이미 등록된 채널입니다.', 'warning');
            } else {
                showMessage(errorMsg, 'error');
            }
            return;
        }
        
        showMessage(`채널 "${result.title}"이(가) 추가되었습니다.`, 'success');
        document.getElementById('channelId').value = '';
        loadChannels();
    } catch (error) {
        console.error('채널 추가 중 오류:', error);
        showMessage('서버 연결 중 오류가 발생했습니다. 나중에 다시 시도해주세요.', 'error');
    }
}

async function deleteChannel(channelId) {
    if (!confirm('이 채널을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        console.log(`채널 삭제 요청: ${channelId}`);
        
        // URL에 포함될 수 있는 특수문자 인코딩
        const encodedChannelId = encodeURIComponent(channelId);
        console.log(`인코딩된 채널 ID: ${encodedChannelId}`);
        
        showMessage('채널 삭제 중...', 'info');
        
        const response = await fetch(`/api/v1/youtube/channels/${encodedChannelId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            let errorMessage = '채널 삭제 실패';
            try {
                if (response.headers.get('content-type')?.includes('application/json')) {
                    const error = await response.json();
                    errorMessage = error.detail || errorMessage;
                } else {
                    errorMessage = `채널 삭제 실패 (상태 코드: ${response.status})`;
                }
            } catch (parseError) {
                console.error('응답 파싱 오류:', parseError);
            }
            console.error(`채널 삭제 실패 (${response.status}): ${errorMessage}`);
            throw new Error(errorMessage);
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
        showMessage(`'${channelId}' 채널의 영상 불러오는 중...`, 'info');
        
        // URL에 포함될 수 있는 특수문자 인코딩
        const encodedChannelId = encodeURIComponent(channelId);
        console.log(`채널 비디오 검색 요청: ${channelId} (인코딩: ${encodedChannelId})`);
        
        const response = await fetch(`/api/v1/youtube/search/by-channel/${encodedChannelId}`);
        
        if (!response.ok) {
            let errorData = { detail: '채널 영상을 불러오는 데 실패했습니다.' };
            try {
                errorData = await response.json();
            } catch (parseError) {
                console.error('오류 응답 파싱 실패:', parseError);
            }
            
            console.error('채널 영상 로드 오류:', errorData);
            
            // 오류 유형에 따른 맞춤형 메시지
            if (response.status === 404) {
                showMessage('등록된 채널을 찾을 수 없습니다. 다시 시도해주세요.', 'error');
            } else {
                showMessage(errorData.detail || '채널 영상을 불러오는 데 실패했습니다.', 'error');
            }
            return;
        }
        
        const videos = await response.json();
        
        if (videos.length === 0) {
            showMessage(`'${channelId}' 채널에서 영상을 찾을 수 없습니다. 채널 ID를 확인해주세요.`, 'warning');
            displayVideos([]); // 빈 결과 표시
            return;
        }
        
        showMessage(`'${channelId}' 채널의 영상 ${videos.length}개를 불러왔습니다.`, 'success');
        displayVideos(videos);
    } catch (error) {
        console.error('채널 영상 로드 중 오류:', error);
        showMessage('채널 영상을 불러오는 데 실패했습니다. 네트워크 연결을 확인해주세요.', 'error');
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

// 전역 변수: 현재 비디오 목록 (필터링용)
let currentVideos = [];

// 영상 표시 함수
function displayVideos(videos) {
    // 전역 변수에 비디오 목록 저장 (필터링을 위해)
    currentVideos = videos;
    
    const videoContainer = document.getElementById('videoResults');
    const videoFilters = document.getElementById('videoFilters');
    const resultCount = document.getElementById('resultCount');
    
    videoContainer.innerHTML = '';
    
    if (videos.length === 0) {
        videoFilters.style.display = 'none';
        videoContainer.innerHTML = '<p class="no-results">검색 결과가 없습니다.</p>';
        return;
    }
    
    // 필터 컨트롤 표시
    videoFilters.style.display = 'flex';
    resultCount.textContent = `총 ${videos.length}개 영상`;
    
    // 초기 정렬: 최신순
    sortVideos('date_desc');
}

// 비디오 목록 렌더링
function renderVideos(videos) {
    const videoContainer = document.getElementById('videoResults');
    videoContainer.innerHTML = '';
    
    videos.forEach(video => {
        // ISO 날짜 형식을 한국어 날짜 형식으로 변환
        const publishDate = video.published_at ? new Date(video.published_at) : null;
        const formattedDate = publishDate ? 
            `${publishDate.getFullYear()}년 ${publishDate.getMonth() + 1}월 ${publishDate.getDate()}일` : 
            '날짜 정보 없음';
            
        // 조회수 형식화 (예: 1,234,567 -> 123.4만)
        const viewCount = formatViewCount(video.view_count);
        
        const videoItem = document.createElement('div');
        videoItem.className = 'video-item';
        videoItem.innerHTML = `
            <img src="${video.thumbnail || 'https://via.placeholder.com/480x360?text=No+Thumbnail'}" 
                 alt="${video.title}" class="video-thumbnail">
            <div class="video-info">
                <h3 title="${video.title}">${video.title}</h3>
                <p class="video-description">${video.description ? video.description.substring(0, 100) + (video.description.length > 100 ? '...' : '') : '설명 없음'}</p>
                <div class="video-meta">
                    <span class="views"><i class="fas fa-eye"></i> ${viewCount}</span>
                    <span class="date"><i class="fas fa-calendar-alt"></i> ${formattedDate}</span>
                </div>
                <div class="video-actions">
                    <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank">
                        <button>유튜브에서 보기</button>
                    </a>
                    <button onclick="summarizeVideo('${video.video_id}')">요약하기</button>
                </div>
            </div>
        `;
        videoContainer.appendChild(videoItem);
    });
}

// 조회수 형식화 함수
function formatViewCount(count) {
    if (!count && count !== 0) return '조회수 정보 없음';
    
    if (count >= 10000000) { // 1000만 이상
        return (count / 10000000).toFixed(1) + '천만';
    } else if (count >= 10000) { // 1만 이상
        return (count / 10000).toFixed(1) + '만';
    } else if (count >= 1000) { // 1천 이상
        return (count / 1000).toFixed(1) + '천';
    } else {
        return count.toString();
    }
}

// 비디오 정렬 함수
function sortVideos(sortBy) {
    if (currentVideos.length === 0) return;
    
    const sortedVideos = [...currentVideos];
    
    switch (sortBy) {
        case 'date_desc': // 최신순
            sortedVideos.sort((a, b) => new Date(b.published_at || 0) - new Date(a.published_at || 0));
            break;
        case 'date_asc': // 오래된순
            sortedVideos.sort((a, b) => new Date(a.published_at || 0) - new Date(b.published_at || 0));
            break;
        case 'views_desc': // 조회수 높은순
            sortedVideos.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
            break;
        case 'views_asc': // 조회수 낮은순
            sortedVideos.sort((a, b) => (a.view_count || 0) - (b.view_count || 0));
            break;
        case 'title_asc': // 제목 오름차순
            sortedVideos.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
            break;
        case 'title_desc': // 제목 내림차순
            sortedVideos.sort((a, b) => (b.title || '').localeCompare(a.title || ''));
            break;
        default:
            break;
    }
    
    // 정렬된 목록 렌더링
    renderVideos(sortedVideos);
}

// 비디오 검색 필터링 함수
function filterVideos(searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') {
        // 검색어가 없으면 현재 정렬 기준으로 모든 비디오 표시
        sortVideos(document.getElementById('videoSortSelect').value);
        return;
    }
    
    searchTerm = searchTerm.toLowerCase().trim();
    
    const filteredVideos = currentVideos.filter(video => 
        (video.title && video.title.toLowerCase().includes(searchTerm)) || 
        (video.description && video.description.toLowerCase().includes(searchTerm))
    );
    
    renderVideos(filteredVideos);
    
    // 검색 결과 카운트 업데이트
    document.getElementById('resultCount').textContent = 
        `검색결과: ${filteredVideos.length}/${currentVideos.length}개 영상`;
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
    
    // 비디오 필터 이벤트 연결
    const videoSearchInput = document.getElementById('videoSearchInput');
    if (videoSearchInput) {
        videoSearchInput.addEventListener('input', function() {
            filterVideos(this.value);
        });
    }
    
    // 비디오 정렬 이벤트 연결
    const videoSortSelect = document.getElementById('videoSortSelect');
    if (videoSortSelect) {
        videoSortSelect.addEventListener('change', function() {
            sortVideos(this.value);
        });
    }
    
    // Font Awesome 아이콘 추가 (CDN에서 로딩)
    if (!document.getElementById('font-awesome')) {
        const fontAwesome = document.createElement('link');
        fontAwesome.id = 'font-awesome';
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
        document.head.appendChild(fontAwesome);
    }
}); 