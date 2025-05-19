// 채널 관련 기능
document.addEventListener('DOMContentLoaded', () => {
    loadChannels();
    setupChannelForm();
});

// 채널 목록 로드
async function loadChannels() {
    try {
        const response = await fetch(`${apiBaseUrl}/channels/`);
        const channels = await response.json();
        
        const channelsList = document.getElementById('channels-list');
        
        if (channels.length === 0) {
            channelsList.innerHTML = '<div class="text-center py-4 text-gray-500">등록된 채널이 없습니다</div>';
            return;
        }
        
        channelsList.innerHTML = channels.map(channel => `
            <div class="py-4 flex items-center justify-between" data-channel-id="${channel.channel_id}">
                <div>
                    <h3 class="font-semibold text-gray-800">${channel.title}</h3>
                    <p class="text-sm text-gray-500">채널 ID: ${channel.channel_id}</p>
                    <p class="text-sm text-gray-600">${channel.description || '설명 없음'}</p>
                    <p class="text-xs text-gray-400">등록일: ${formatDate(channel.created_at)}</p>
                </div>
                <div class="flex space-x-2">
                    <button class="edit-channel text-blue-500 hover:text-blue-700" title="수정">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-channel text-red-500 hover:text-red-700" title="삭제">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // 채널 수정 버튼 이벤트
        document.querySelectorAll('.edit-channel').forEach(button => {
            button.addEventListener('click', (e) => {
                const channelElement = e.target.closest('[data-channel-id]');
                const channelId = channelElement.dataset.channelId;
                editChannel(channelId);
            });
        });
        
        // 채널 삭제 버튼 이벤트
        document.querySelectorAll('.delete-channel').forEach(button => {
            button.addEventListener('click', (e) => {
                const channelElement = e.target.closest('[data-channel-id]');
                const channelId = channelElement.dataset.channelId;
                deleteChannel(channelId);
            });
        });
        
    } catch (error) {
        console.error('채널 목록을 불러오는 중 오류 발생:', error);
    }
}

// 채널 추가 폼 설정
function setupChannelForm() {
    const form = document.getElementById('channel-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const channelId = document.getElementById('channel-id').value;
        const title = document.getElementById('channel-title').value;
        const description = document.getElementById('channel-description').value;
        
        try {
            const response = await fetch(`${apiBaseUrl}/channels/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    title: title || undefined,
                    description: description || undefined
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '채널을 추가하는 중 오류가 발생했습니다');
            }
            
            // 폼 초기화
            form.reset();
            
            // 채널 목록 새로고침
            loadChannels();
            
            // 성공 메시지
            showModal('성공', '<p class="text-green-600">채널이 성공적으로 추가되었습니다!</p>');
            
        } catch (error) {
            console.error('채널 추가 중 오류 발생:', error);
            showModal('오류', `<p class="text-red-600">${error.message}</p>`);
        }
    });
}

// 채널 수정
async function editChannel(channelId) {
    try {
        const response = await fetch(`${apiBaseUrl}/channels/${channelId}`);
        const channel = await response.json();
        
        const modalContent = `
            <form id="edit-channel-form" class="space-y-4">
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-channel-id">
                        채널 ID (수정 불가)
                    </label>
                    <input
                        id="edit-channel-id"
                        type="text"
                        class="w-full px-3 py-2 text-gray-500 border rounded-lg bg-gray-100"
                        value="${channel.channel_id}"
                        readonly
                    >
                </div>
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-channel-title">
                        채널 제목
                    </label>
                    <input
                        id="edit-channel-title"
                        type="text"
                        class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:shadow-outline"
                        value="${channel.title}"
                        required
                    >
                </div>
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-channel-description">
                        설명
                    </label>
                    <textarea
                        id="edit-channel-description"
                        class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:shadow-outline"
                        rows="2"
                    >${channel.description || ''}</textarea>
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
        
        showModal('채널 수정', modalContent);
        
        // 수정 폼 이벤트 리스너
        document.getElementById('edit-channel-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const title = document.getElementById('edit-channel-title').value;
            const description = document.getElementById('edit-channel-description').value;
            
            try {
                const response = await fetch(`${apiBaseUrl}/channels/${channelId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        channel_id: channelId,
                        title: title,
                        description: description || undefined
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || '채널을 수정하는 중 오류가 발생했습니다');
                }
                
                // 모달 닫기
                document.getElementById('modal').classList.add('hidden');
                
                // 채널 목록 새로고침
                loadChannels();
                
                // 성공 메시지
                showModal('성공', '<p class="text-green-600">채널이 성공적으로 수정되었습니다!</p>');
                
            } catch (error) {
                console.error('채널 수정 중 오류 발생:', error);
                showModal('오류', `<p class="text-red-600">${error.message}</p>`);
            }
        });
        
    } catch (error) {
        console.error('채널 정보를 불러오는 중 오류 발생:', error);
        showModal('오류', '<p class="text-red-600">채널 정보를 불러오는 중 오류가 발생했습니다</p>');
    }
}

// 채널 삭제
async function deleteChannel(channelId) {
    const modalContent = `
        <p class="mb-4">정말로 이 채널을 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.</p>
        <div class="flex justify-end space-x-2">
            <button id="cancel-delete" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline">
                취소
            </button>
            <button id="confirm-delete" class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline">
                삭제
            </button>
        </div>
    `;
    
    showModal('채널 삭제', modalContent);
    
    // 취소 버튼
    document.getElementById('cancel-delete').addEventListener('click', () => {
        document.getElementById('modal').classList.add('hidden');
    });
    
    // 확인 버튼
    document.getElementById('confirm-delete').addEventListener('click', async () => {
        try {
            const response = await fetch(`${apiBaseUrl}/channels/${channelId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '채널을 삭제하는 중 오류가 발생했습니다');
            }
            
            // 모달 닫기
            document.getElementById('modal').classList.add('hidden');
            
            // 채널 목록 새로고침
            loadChannels();
            
            // 성공 메시지
            showModal('성공', '<p class="text-green-600">채널이 성공적으로 삭제되었습니다!</p>');
            
        } catch (error) {
            console.error('채널 삭제 중 오류 발생:', error);
            showModal('오류', `<p class="text-red-600">${error.message}</p>`);
        }
    });
} 