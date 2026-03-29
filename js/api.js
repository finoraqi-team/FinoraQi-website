class APIClient {
    async processPayment(data) {
        const response = await fetch(`${API_BASE}/api/v1/payment/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    }
}
