const axios = require('axios');
const crypto = require('crypto');
const fs = require('fs');

// Load config
const config = JSON.parse(fs.readFileSync('Asset.config', 'utf8'));

const apiSecret = config.apiSecret;
const apiKey = config.apiKey;
const passphrase = config.passphrase;

const timestamp = Date.now() / 1000; // Timestamp in seconds
const requestPath = '/accounts';
const method = 'GET';
const body = '';

const what = timestamp + method + requestPath + body;
const key = Buffer.from(apiSecret, 'base64');
const hmac = crypto.createHmac('sha256', key);
const sign = hmac.update(what).digest('base64');

let configRequest = {
    method: method,
    url: `https://api-public.sandbox.pro.coinbase.com${requestPath}`,
    headers: {
        'CB-ACCESS-KEY': apiKey,
        'CB-ACCESS-SIGN': sign,
        'CB-ACCESS-TIMESTAMP': timestamp.toString(),
        'CB-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
};

axios.request(configRequest)
.then((response) => {
    const accountInfo = response.data.map(account => ({
        id: account.id,
        display_name: `${account.currency} Account`,
        currency: account.currency,
        balance: account.balance,
        available: account.available,
        hold: account.hold,
        trading_enabled: account.trading_enabled,
        pending_deposit: account.pending_deposit
    }));
    process.stdout.write(JSON.stringify(accountInfo)); // Send data to stdout
})
.catch((error) => {
    console.error('Error fetching sandbox assets:', error);
    process.exit(1); // Exit with an error code
});
