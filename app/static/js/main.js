document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('summarize-form');
    const resultDiv = document.getElementById('result');
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const textInput = document.getElementById('text').value;
            const styleSelect = document.getElementById('style').value;
            const maxLengthInput = document.getElementById('max_length').value;
            const languageSelect = document.getElementById('language').value;
            const formatSelect = document.getElementById('format').value;
            
            if (!textInput) {
                alert('텍스트를 입력해주세요.');
                return;
            }
            
            try {
                resultDiv.innerHTML = '<p>요약 중...</p>';
                
                const response = await fetch('/api/v1/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: textInput,
                        style: styleSelect,
                        max_length: parseInt(maxLengthInput),
                        language: languageSelect,
                        format: formatSelect
                    }),
                });
                
                if (!response.ok) {
                    throw new Error('요약 과정에서 오류가 발생했습니다.');
                }
                
                const data = await response.json();
                
                let resultHTML = `<h3>요약 결과</h3>
                                 <div class="summary">${data.summary}</div>`;
                
                if (data.key_phrases && data.key_phrases.length > 0) {
                    resultHTML += `<h4>핵심 문구</h4>
                                  <ul>
                                      ${data.key_phrases.map(phrase => `<li>${phrase}</li>`).join('')}
                                  </ul>`;
                }
                
                if (data.quality_score) {
                    resultHTML += `<h4>요약 품질 점수</h4>
                                  <ul>
                                      ${Object.entries(data.quality_score).map(([key, value]) => 
                                          `<li>${key}: ${value}</li>`).join('')}
                                  </ul>`;
                }
                
                resultDiv.innerHTML = resultHTML;
                
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = `<p class="error">오류: ${error.message}</p>`;
            }
        });
    }
}); 