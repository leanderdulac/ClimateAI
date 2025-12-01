// Test script to verify environment variables and API calls
console.log('=== Environment Variables ===');
console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
console.log('VITE_USE_MOCK_DATA:', import.meta.env.VITE_USE_MOCK_DATA);
console.log('');

// Test API call
console.log('=== Testing API Call ===');
const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
const testUrl = baseUrl ? `${baseUrl}/localizacao/cidade/busca?termo=gramado` : '/api/v1/localizacao/cidade/busca?termo=gramado';
console.log('Test URL:', testUrl);

fetch(testUrl)
    .then(res => res.json())
    .then(data => {
        console.log('✅ API Response:', data);
        console.log(`Found ${data.length} cities`);
        if (data.length > 0) {
            console.log('First city:', data[0]);
        }
    })
    .catch(err => {
        console.error('❌ API Error:', err);
    });
