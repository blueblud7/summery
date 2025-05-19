// 키워드 관련 기능
document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    setupKeywordForm();
});

// 키워드 목록 로드
async function loadKeywords() {
    try {
        const response = await fetch(`${apiBaseUrl}/keywords/`);
        const keywords = await response.json();
        
        const keywordsList = document.getElementById('keywords-list');
        
        if (keywords.length === 0) {
            keywordsList.innerHTML = '<div class="text-center py-4 text-gray-500">등록된 키워드가 없습니다</div>';
            return;
        }
        
        keywordsList.innerHTML = keywords.map(keyword => `
            <div class="py-4 flex items-center justify-between" data-keyword="${keyword.keyword}">
                <div>
                    <h3 class="font-semibold text-gray-800">${keyword.keyword}</h3>
                    <p class="text-sm text-gray-600">${keyword.description || '설명 없음'}</p>
                    <p class="text-xs text-gray-400">등록일: ${formatDate(keyword.created_at)}</p>
                </div>
                <div class="flex space-x-2">
                    <button class="edit-keyword text-blue-500 hover:text-blue-700" title="수정">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-keyword text-red-500 hover:text-red-700" title="삭제">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // 키워드 수정 버튼 이벤트
        document.querySelectorAll('.edit-keyword').forEach(button => {
            button.addEventListener('click', (e) => {
                const keywordElement = e.target.closest('[data-keyword]');
                const keyword = keywordElement.dataset.keyword;
                editKeyword(keyword);
            });
        });
        
        // 키워드 삭제 버튼 이벤트
        document.querySelectorAll('.delete-keyword').forEach(button => {
            button.addEventListener('click', (e) => {
                const keywordElement = e.target.closest('[data-keyword]');
                const keyword = keywordElement.dataset.keyword;
                deleteKeyword(keyword);
            });
        });
        
    } catch (error) {
        console.error('키워드 목록을 불러오는 중 오류 발생:', error);
    }
}

// 키워드 추가 폼 설정
function setupKeywordForm() {
    const form = document.getElementById('keyword-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const keyword = document.getElementById('keyword').value;
        const description = document.getElementById('keyword-description').value;
        
        try {
            const response = await fetch(`${apiBaseUrl}/keywords/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: keyword,
                    description: description || undefined
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '키워드를 추가하는 중 오류가 발생했습니다');
            }
            
            // 폼 초기화
            form.reset();
            
            // 키워드 목록 새로고침
            loadKeywords();
            
            // 성공 메시지
            showModal('성공', '<p class="text-green-600">키워드가 성공적으로 추가되었습니다!</p>');
            
        } catch (error) {
            console.error('키워드 추가 중 오류 발생:', error);
            showModal('오류', `<p class="text-red-600">${error.message}</p>`);
        }
    });
}

// 키워드 수정
async function editKeyword(keyword) {
    try {
        const response = await fetch(`${apiBaseUrl}/keywords/${encodeURIComponent(keyword)}`);
        const keywordData = await response.json();
        
        const modalContent = `
            <form id="edit-keyword-form" class="space-y-4">
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-keyword">
                        키워드 (수정 불가)
                    </label>
                    <input
                        id="edit-keyword"
                        type="text"
                        class="w-full px-3 py-2 text-gray-500 border rounded-lg bg-gray-100"
                        value="${keywordData.keyword}"
                        readonly
                    >
                </div>
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-keyword-description">
                        설명
                    </label>
                    <textarea
                        id="edit-keyword-description"
                        class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:shadow-outline"
                        rows="2"
                    >${keywordData.description || ''}</textarea>
                </div>
                <div class="flex justify-end">
                    <button
                        type="submit"
                        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline"
                    >
                        저장
                    </button>
                </div>
            </form>
        `;
        
        showModal('키워드 수정', modalContent);
        
        // 수정 폼 이벤트 리스너
        document.getElementById('edit-keyword-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const description = document.getElementById('edit-keyword-description').value;
            
            try {
                const response = await fetch(`${apiBaseUrl}/keywords/${encodeURIComponent(keyword)}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        keyword: keyword,
                        description: description || undefined
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || '키워드를 수정하는 중 오류가 발생했습니다');
                }
                
                // 모달 닫기
                document.getElementById('modal').classList.add('hidden');
                
                // 키워드 목록 새로고침
                loadKeywords();
                
                // 성공 메시지
                showModal('성공', '<p class="text-green-600">키워드가 성공적으로 수정되었습니다!</p>');
                
            } catch (error) {
                console.error('키워드 수정 중 오류 발생:', error);
                showModal('오류', `<p class="text-red-600">${error.message}</p>`);
            }
        });
        
    } catch (error) {
        console.error('키워드 정보를 불러오는 중 오류 발생:', error);
        showModal('오류', '<p class="text-red-600">키워드 정보를 불러오는 중 오류가 발생했습니다</p>');
    }
}

// 키워드 삭제
async function deleteKeyword(keyword) {
    const modalContent = `
        <p class="mb-4">정말로 이 키워드를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.</p>
        <div class="flex justify-end space-x-2">
            <button id="cancel-delete" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline">
                취소
            </button>
            <button id="confirm-delete" class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline">
                삭제
            </button>
        </div>
    `;
    
    showModal('키워드 삭제', modalContent);
    
    // 취소 버튼
    document.getElementById('cancel-delete').addEventListener('click', () => {
        document.getElementById('modal').classList.add('hidden');
    });
    
    // 확인 버튼
    document.getElementById('confirm-delete').addEventListener('click', async () => {
        try {
            const response = await fetch(`${apiBaseUrl}/keywords/${encodeURIComponent(keyword)}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '키워드를 삭제하는 중 오류가 발생했습니다');
            }
            
            // 모달 닫기
            document.getElementById('modal').classList.add('hidden');
            
            // 키워드 목록 새로고침
            loadKeywords();
            
            // 성공 메시지
            showModal('성공', '<p class="text-green-600">키워드가 성공적으로 삭제되었습니다!</p>');
            
        } catch (error) {
            console.error('키워드 삭제 중 오류 발생:', error);
            showModal('오류', `<p class="text-red-600">${error.message}</p>`);
        }
    });
} 