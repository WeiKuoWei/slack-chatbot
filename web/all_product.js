const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Define the configuration for the GET request
let config = {
  method: 'get',
  url: 'https://api.exchange.coinbase.com/products',
  headers: { 
    'Content-Type': 'application/json'
  }
};

// Function to save data to JSON
const saveToJson = (data, outputFile) => {
  fs.writeFile(outputFile, JSON.stringify(data, null, 4), (err) => {
    if (err) {
      console.error('Error writing to file:', err);
    } else {
      console.log(`Output written to ${outputFile}`);
    }
  });
};

// Function to parse and structure the data
const parseAndSaveData = (products) => {
  let currencyDict = {};

  if (Array.isArray(products)) {
    products.forEach((product) => {
      const { base_currency, quote_currency } = product;
      if (!currencyDict[base_currency]) {
        currencyDict[base_currency] = [];
      }
      currencyDict[base_currency].push(quote_currency);
    });
  } else {
    console.error('Unexpected response format:', JSON.stringify(products, null, 2));
    return;
  }

  // Sorting the quote currencies for each base currency
  for (let base in currencyDict) {
    currencyDict[base].sort();
  }

  // Convert to sorted array for consistent order
  let sortedCurrencyDict = Object.keys(currencyDict).sort().reduce((acc, key) => {
    acc[key] = currencyDict[key];
    return acc;
  }, {});

  saveToJson(sortedCurrencyDict, path.join(__dirname, 'frontend/src/currencyPairs.json'));
};

// Send the request
axios.request(config)
  .then((response) => {
    parseAndSaveData(response.data);
  })
  .catch((error) => {
    console.error('Error fetching data:', error.message);
  });
