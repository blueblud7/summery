// 검색 관련 기능
document.addEventListener('DOMContentLoaded', () => {
    setupSearchForm();
    updateSearchDropdown();
});

// 검색 폼 설정
function setupSearchForm() {
    const searchTypeSelect = document.getElementById('search-type');
    const searchBtn = document.getElementById('search-btn');

    // 검색 유형 변경 시 드롭다운 업데이트
    searchTypeSelect.addEventListener('change', () => {
        updateSearchDropdown();
    });

    // 검색 버튼 클릭 이벤트
    searchBtn.addEventListener('click', () => {
        const searchType = searchTypeSelect.value;
        const searchQuery = document.getElementById('search-query').value;

        if (!searchQuery) {
            showModal('오류', '<p class="text-red-600">검색어를 선택해주세요</p>');
            return;
        }

        performSearch(searchType, searchQuery);
    });
}

// 검색 드롭다운 업데이트
async function updateSearchDropdown() {
    const searchType = document.getElementById('search-type').value;
    const searchQuerySelect = document.getElementById('search-query');
    
    // 드롭다운 초기화
    searchQuerySelect.innerHTML = '<option value="">선택하세요</option>';
    
    try {
        let items = [];
        if (searchType === 'channel') {
            // 채널 목록 가져오기
            const response = await fetch(`${apiBaseUrl}/channels/`);
            items = await response.json();
            
            // 채널 옵션 추가
            items.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.channel_id;
                option.textContent = `${channel.title} (${channel.channel_id})`;
                searchQuerySelect.appendChild(option);
            });
        } else if (searchType === 'keyword') {
            // 키워드 목록 가져오기
            const response = await fetch(`${apiBaseUrl}/keywords/`);
            items = await response.json();
            
            // 키워드 옵션 추가
            items.forEach(keyword => {
                const option = document.createElement('option');
                option.value = keyword.keyword;
                option.textContent = keyword.keyword;
                searchQuerySelect.appendChild(option);
            });
        }
        
        // 항목이 없는 경우 메시지 표시
        if (items.length === 0) {
            const option = document.createElement('option');
            option.value = "";
            option.textContent = searchType === 'channel' ? '등록된 채널이 없습니다' : '등록된 키워드가 없습니다';
            searchQuerySelect.appendChild(option);
        }
    } catch (error) {
        console.error('검색 옵션을 불러오는 중 오류 발생:', error);
        
        // 에러 메시지 옵션 추가
        const option = document.createElement('option');
        option.value = "";
        option.textContent = '데이터를 불러올 수 없습니다';
        searchQuerySelect.appendChild(option);
    }
}

// 검색 수행
async function performSearch(type, query) {
    const searchResults = document.getElementById('search-results');
    
    // 로딩 메시지 표시
    searchResults.innerHTML = '<div class="text-center py-4 text-gray-500 col-span-2">검색 중...</div>';
    
    try {
        let response;
        if (type === 'channel') {
            response = await fetch(`${apiBaseUrl}/search/by-channel/${query}`);
        } else if (type === 'keyword') {
            response = await fetch(`${apiBaseUrl}/search/by-keyword/${encodeURIComponent(query)}`);
        }
        
        if (!response.ok) {
            throw new Error('검색 결과를 가져오는 중 오류가 발생했습니다');
        }
        
        const videos = await response.json();
        
        // 검색 결과가 없는 경우
        if (videos.length === 0) {
            searchResults.innerHTML = '<div class="text-center py-4 text-gray-500 col-span-2">검색 결과가 없습니다</div>';
            return;
        }
        
        // 검색 결과 표시
        searchResults.innerHTML = videos.map(video => `
            <div class="bg-gray-50 p-4 rounded-lg">
                <h3 class="font-semibold text-gray-800 mb-2">${video.title}</h3>
                <p class="text-sm text-gray-600 mb-2">${video.description ? video.description.substring(0, 100) + '...' : '설명 없음'}</p>
                <div class="flex justify-between items-center">
                    <span class="text-xs text-gray-500">${formatDate(video.published_at)}</span>
                    <a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank" class="text-blue-500 hover:text-blue-700">
                        <i class="fas fa-external-link-alt mr-1"></i>보기
                    </a>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('검색 중 오류 발생:', error);
        searchResults.innerHTML = `<div class="text-center py-4 text-red-500 col-span-2">오류: ${error.message}</div>`;
    }
} 