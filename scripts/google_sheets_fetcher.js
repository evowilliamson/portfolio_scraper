/**
 * Jupiter Portfolio Fetcher for Google Sheets
 * 
 * This script:
 * 1. Reads the wallet address from cell B1 in "solana_portfolio" sheet
 * 2. Calls the Flask API endpoint to get portfolio data
 * 3. Writes the portfolio data starting from row 3
 * 
 * Setup:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Update the API_URL constant with your server URL
 * 5. Run the function or create a menu item
 */

// Configuration
const API_URL = "https://nondefensible-unbridled-zainab.ngrok-free.dev/portfolio"; // FIXED: Use HTTPS
const SHEET_NAME = "solana_portfolio";

/**
 * Fetches portfolio data from the Flask API and writes it to the sheet
 */
function fetchJupiterPortfolio() {
  try {
    Logger.log("=== Starting fetchJupiterPortfolio ===");
    
    // Get the active spreadsheet and sheet
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    Logger.log(`Spreadsheet: ${spreadsheet.getName()}`);
    
    const sheet = spreadsheet.getSheetByName(SHEET_NAME);
    
    if (!sheet) {
      const errorMsg = `Sheet "${SHEET_NAME}" not found!`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    Logger.log(`Sheet found: ${SHEET_NAME}`);
    
    // Read wallet address from cell B1
    const walletAddress = sheet.getRange("B1").getValue();
    Logger.log(`Raw wallet address from B1: "${walletAddress}"`);
    
    if (!walletAddress || walletAddress.toString().trim() === "") {
      const errorMsg = "Wallet address in cell B1 is empty!";
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    const trimmedAddress = walletAddress.toString().trim();
    Logger.log(`Trimmed wallet address: "${trimmedAddress}"`);
    Logger.log(`Fetching portfolio for wallet: ${trimmedAddress}`);
    
    // Call the Flask API
    const url = `${API_URL}?address=${encodeURIComponent(trimmedAddress)}`;
    Logger.log(`Full API URL: ${url}`);
    
    Logger.log("Calling API...");
    const startTime = new Date().getTime();
    
    const response = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true,
      headers: {
        "Accept": "application/json",
        "User-Agent": "GoogleSheets/1.0",
        "ngrok-skip-browser-warning": "true"  // Bypass ngrok interstitial page
      }
    });
    
    const endTime = new Date().getTime();
    Logger.log(`API call took ${endTime - startTime}ms`);
    
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    const responseHeaders = response.getHeaders();
    
    Logger.log(`Response code: ${responseCode}`);
    Logger.log(`Response headers: ${JSON.stringify(responseHeaders)}`);
    Logger.log(`Response length: ${responseText.length} characters`);
    Logger.log(`Response content (first 500 chars): ${responseText.substring(0, 500)}`);
    
    if (responseCode !== 200) {
      const errorMsg = `API Error: ${responseCode}\n\nResponse:\n${responseText.substring(0, 1000)}`;
      Logger.log(`ERROR: Non-200 response - ${errorMsg}`);
      return;
    }
    
    // Check if response is HTML (ngrok warning page)
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      const errorMsg = "ERROR: Received HTML instead of JSON!\n\n" +
                       "This usually means:\n" +
                       "1. Ngrok is showing a warning page (visit the URL in browser first)\n" +
                       "2. The API URL is incorrect\n" +
                       "3. The API server is not running\n\n" +
                       "Visit this URL in your browser first:\n" + url;
      Logger.log(`ERROR: ${errorMsg}`);
      Logger.log(`HTML Response: ${responseText.substring(0, 1000)}`);
      return;
    }
    
    // Parse the JSON response
    Logger.log("Parsing JSON response...");
    let portfolioData;
    try {
      portfolioData = JSON.parse(responseText);
      Logger.log("JSON parsed successfully");
      Logger.log(`Projects count: ${portfolioData.projects ? portfolioData.projects.length : 0}`);
    } catch (parseError) {
      const errorMsg = `JSON Parse Error: ${parseError.toString()}\n\n` +
                       `Response (first 1000 chars):\n${responseText.substring(0, 1000)}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check for API error response
    if (portfolioData.error) {
      const errorMsg = `API returned error: ${portfolioData.error}\n${portfolioData.message || ""}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check if we have projects data
    if (!portfolioData.projects || portfolioData.projects.length === 0) {
      const errorMsg = "No portfolio projects found in response";
      Logger.log(`WARNING: ${errorMsg}`);
      return;
    }
    
    Logger.log("Clearing existing data...");
    // Clear existing data (from row 3 onwards)
    const lastRow = sheet.getLastRow();
    if (lastRow >= 3) {
      sheet.getRange(3, 1, lastRow - 2, sheet.getLastColumn()).clearContent();
      Logger.log(`Cleared rows 3-${lastRow}`);
    }
    
    // Write headers in row 2
    Logger.log("Writing headers...");
    const headers = ["Project", "Section Type", "Market/Type", "Token", "Balance", "Yield (%)", "Value ($)"];
    sheet.getRange(2, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(2, 1, 1, headers.length).setFontWeight("bold");
    
    // Prepare data rows
    const dataRows = [];
    Logger.log("Processing projects...");
    
    // Process each project
    for (const project of portfolioData.projects) {
      const projectName = project.project_name;
      Logger.log(`  Processing project: ${projectName} (${project.sections ? project.sections.length : 0} sections)`);
      
      if (!project.sections) {
        Logger.log(`    WARNING: No sections found for project ${projectName}`);
        continue;
      }
      
      for (const section of project.sections) {
        const sectionType = section.section_type;
        Logger.log(`    Processing section: ${sectionType}`);
        
        if (sectionType === "Farming") {
          // Process farming assets
          const assetCount = section.assets ? section.assets.length : 0;
          Logger.log(`      Farming assets: ${assetCount}`);
          
          if (section.assets) {
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                sectionType,
                "Farming",
                asset.token,
                asset.balance,
                asset.yield,
                asset.value
              ]);
            }
          }
        } else if (sectionType === "Lending") {
          const marketName = section.market_name || "Unknown Market";
          const suppliedCount = section.supplied ? section.supplied.length : 0;
          const borrowedCount = section.borrowed ? section.borrowed.length : 0;
          Logger.log(`      Lending market: ${marketName} (${suppliedCount} supplied, ${borrowedCount} borrowed)`);
          
          // Process supplied assets
          if (section.supplied) {
            for (const asset of section.supplied) {
              dataRows.push([
                projectName,
                sectionType,
                `${marketName} (Supplied)`,
                asset.token,
                asset.balance,
                asset.yield,
                asset.value
              ]);
            }
          }
          
          // Process borrowed assets
          if (section.borrowed) {
            for (const asset of section.borrowed) {
              dataRows.push([
                projectName,
                sectionType,
                `${marketName} (Borrowed)`,
                asset.token,
                asset.balance,
                asset.yield,
                asset.value
              ]);
            }
          }
        }
      }
    }
    
    Logger.log(`Total data rows prepared: ${dataRows.length}`);
    
    // Write data starting from row 3
    if (dataRows.length > 0) {
      Logger.log("Writing data to sheet...");
      sheet.getRange(3, 1, dataRows.length, headers.length).setValues(dataRows);
      
      Logger.log("Formatting cells...");
      // Format the sheet
      sheet.getRange(3, 5, dataRows.length, 1).setNumberFormat("#,##0.00"); // Balance
      sheet.getRange(3, 6, dataRows.length, 1).setNumberFormat("0.00"); // Yield
      sheet.getRange(3, 7, dataRows.length, 1).setNumberFormat("$#,##0.00"); // Value
      
      Logger.log("Auto-resizing columns...");
      // Auto-resize columns
      for (let i = 1; i <= headers.length; i++) {
        sheet.autoResizeColumn(i);
      }
      
      const successMsg = `✓ Successfully fetched portfolio data!\n${dataRows.length} rows imported.`;
      Logger.log(successMsg);
    } else {
      const warningMsg = "No portfolio data found to import.";
      Logger.log(`WARNING: ${warningMsg}`);
    }
    
    // Write metadata to cell A1
    const timestamp = new Date().toLocaleString();
    sheet.getRange("A1").setValue(`Last updated: ${timestamp}`);
    Logger.log(`Updated timestamp: ${timestamp}`);
    
    // Write cache info if available
    if (portfolioData.cached_at) {
      sheet.getRange("A2").setValue(`Data cached at: ${portfolioData.cached_at}`);
      Logger.log(`Cache timestamp: ${portfolioData.cached_at}`);
    }
    
    Logger.log("=== fetchJupiterPortfolio completed successfully ===");
    
  } catch (error) {
    const errorMsg = `Unexpected Error: ${error.toString()}\n\nStack:\n${error.stack}`;
    Logger.log(`FATAL ERROR: ${errorMsg}`);
  }
}

/**
 * Test function to check the API connection
 */
function testAPIConnection() {
  try {
    Logger.log("=== Testing API Connection ===");
    
    const healthUrl = API_URL.replace('/portfolio', '/health');
    Logger.log(`Health check URL: ${healthUrl}`);
    
    const response = UrlFetchApp.fetch(healthUrl, {
      method: "get",
      muteHttpExceptions: true,
      headers: {
        "Accept": "application/json",
        "ngrok-skip-browser-warning": "true"  // Bypass ngrok interstitial page
      }
    });
    
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log(`Response code: ${responseCode}`);
    Logger.log(`Response: ${responseText}`);
    
    if (responseCode === 200) {
      try {
        const healthData = JSON.parse(responseText);
        const msg = `✓ API connection successful!\n\n` +
                    `Status: ${healthData.status}\n` +
                    `Last update: ${healthData.last_update || "N/A"}\n` +
                    `Scrape interval: ${healthData.scrape_interval_minutes || "N/A"} min`;
        Logger.log(msg);
      } catch (e) {
        Logger.log("Response is not valid JSON");
        Logger.log(`✓ API responded (${responseCode}) but response is not JSON:\n${responseText.substring(0, 500)}`);
      }
    } else {
      const msg = `✗ API connection failed: ${responseCode}\n\n${responseText.substring(0, 500)}`;
      Logger.log(msg);
    }
  } catch (error) {
    const msg = `✗ Connection error: ${error.toString()}`;
    Logger.log(msg);
  }
}

/**
 * Creates a custom menu in Google Sheets
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Jupiter Portfolio')
    .addItem('Fetch Portfolio', 'fetchJupiterPortfolio')
    .addItem('Test API Connection', 'testAPIConnection')
    .addToUi();
  
  Logger.log("Custom menu created");
}
