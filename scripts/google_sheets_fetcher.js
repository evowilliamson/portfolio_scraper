

/**
 * Unified Portfolio Fetcher for Google Sheets
 * 
 * This script fetches portfolio data from both Solana (Jupiter) and EVM (DeBank)
 * 
 * Setup:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Update the API_URL constant with your server URL
 * 5. Create two sheets: "solana_portfolio" and "EVM_portfolio"
 * 6. Put wallet addresses in cell B1 of each sheet
 * 7. Run the functions or use the custom menu
 */

/**
 * Runs automatically when the spreadsheet is opened
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Portfolio')
    .addItem('Fetch Solana Portfolio', 'fetchSolanaPortfolio')
    .addItem('Fetch EVM Portfolio', 'fetchEVMPortfolio')
    .addToUi();
}

/**
 * Unified Portfolio Fetcher for Google Sheets
 * 
 * This script fetches portfolio data from both Solana (Jupiter) and EVM (DeBank)
 * 
 * Setup:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Update the API_URL constant with your server URL
 * 5. Create two sheets: "solana_portfolio" and "EVM_portfolio"
 * 6. Put wallet addresses in cell B1 of each sheet
 * 7. Run the functions or use the custom menu
 */

// Configuration
const API_URL = "https://nondefensible-unbridled-zainab.ngrok-free.dev/portfolio";

/**
 * Fetches Solana portfolio data from the Flask API and writes it to the sheet
 */
function fetchSolanaPortfolio() {
  const SHEET_NAME = "solana_portfolio";
  
  try {
    Logger.log("=== Starting fetchSolanaPortfolio ===");
    
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
    
    let trimmedAddress = walletAddress.toString().trim();
    // Normalize EVM addresses to lowercase
    if (trimmedAddress.startsWith('0x')) {
      trimmedAddress = trimmedAddress.toLowerCase();
    }
        
    Logger.log(`Fetching portfolio for wallet: ${trimmedAddress}`);
    
    // Call the Flask API
    const url = `${API_URL}?address=${encodeURIComponent(trimmedAddress)}`;
    Logger.log(`Full API URL: ${url}`);
    
    const startTime = new Date().getTime();
    
    const response = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true,
      headers: {
        "Accept": "application/json",
        "User-Agent": "GoogleSheets/1.0",
        "ngrok-skip-browser-warning": "true"
      }
    });
    
    const endTime = new Date().getTime();
    Logger.log(`API call took ${endTime - startTime}ms`);
    
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log(`Response code: ${responseCode}`);
    
    if (responseCode !== 200) {
      const errorMsg = `API Error: ${responseCode}\n\nResponse:\n${responseText.substring(0, 1000)}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check if response is HTML
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      const errorMsg = "ERROR: Received HTML instead of JSON!\n\nVisit this URL in your browser first:\n" + url;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Parse JSON
    Logger.log("Parsing JSON response...");
    let portfolioData;
    try {
      portfolioData = JSON.parse(responseText);
      Logger.log("JSON parsed successfully");
      Logger.log(`Projects count: ${portfolioData.projects ? portfolioData.projects.length : 0}`);
    } catch (parseError) {
      const errorMsg = `JSON Parse Error: ${parseError.toString()}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check for API error
    if (portfolioData.error) {
      const errorMsg = `API returned error: ${portfolioData.error}\n${portfolioData.message || ""}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    if (!portfolioData.projects || portfolioData.projects.length === 0) {
      Logger.log("WARNING: No portfolio projects found");
      return;
    }
    
    Logger.log("Clearing existing data...");
    const lastRow = sheet.getLastRow();
    if (lastRow >= 3) {
      sheet.getRange(3, 1, lastRow - 2, sheet.getLastColumn()).clearContent();
    }
    
    // Write headers
    Logger.log("Writing headers...");
    const headers = ["Project", "Section Type", "Market/Type", "Token", "Balance", "Yield (%)", "Value ($)"];
    sheet.getRange(2, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(2, 1, 1, headers.length).setFontWeight("bold");
    
    // Prepare data rows
    const dataRows = [];
    Logger.log("Processing projects...");
    
    for (const project of portfolioData.projects) {
      const projectName = project.project_name;
      Logger.log(`  Processing project: ${projectName}`);
      
      if (!project.sections) continue;
      
      for (const section of project.sections) {
        const sectionType = section.section_type;
        Logger.log(`    Processing section type: ${sectionType}`);
        
        // Handle Wallet section (Holdings)
        if (sectionType === "Wallet") {
          if (section.assets) {
            Logger.log(`      Found ${section.assets.length} wallet assets`);
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                sectionType,
                "Holdings",
                asset.token,
                asset.balance,
                "", // No yield for wallet holdings
                asset.value
              ]);
            }
          }
        }
        // Handle Farming section
        else if (sectionType === "Farming") {
          if (section.assets) {
            Logger.log(`      Found ${section.assets.length} farming assets`);
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                sectionType,
                "Farming",
                asset.token,
                asset.balance,
                asset.yield || "",
                asset.value
              ]);
            }
          }
        }
        // Handle Lending section
        else if (sectionType === "Lending") {
          const marketName = section.market_name || "Unknown Market";
          
          if (section.supplied) {
            Logger.log(`      Found ${section.supplied.length} supplied assets`);
            for (const asset of section.supplied) {
              dataRows.push([
                projectName,
                sectionType,
                `${marketName} (Supplied)`,
                asset.token,
                asset.balance,
                asset.yield || "",
                asset.value
              ]);
            }
          }
          
          if (section.borrowed) {
            Logger.log(`      Found ${section.borrowed.length} borrowed assets`);
            for (const asset of section.borrowed) {
              dataRows.push([
                projectName,
                sectionType,
                `${marketName} (Borrowed)`,
                asset.token,
                asset.balance,
                asset.yield || "",
                asset.value
              ]);
            }
          }
        }
      }
    }
    
    Logger.log(`Total data rows prepared: ${dataRows.length}`);
    
    if (dataRows.length > 0) {
      Logger.log("Writing data to sheet...");
      sheet.getRange(3, 1, dataRows.length, headers.length).setValues(dataRows);
      
      // Format cells
      sheet.getRange(3, 5, dataRows.length, 1).setNumberFormat("#,##0.00");
      sheet.getRange(3, 6, dataRows.length, 1).setNumberFormat("0.00");
      sheet.getRange(3, 7, dataRows.length, 1).setNumberFormat("$#,##0.00");
      
      // Auto-resize columns
      for (let i = 1; i <= headers.length; i++) {
        sheet.autoResizeColumn(i);
      }
      
      Logger.log(`✓ Successfully fetched portfolio data! ${dataRows.length} rows imported.`);
    } else {
      Logger.log("WARNING: No portfolio data found");
    }
    
    // Write metadata
    const timestamp = new Date().toLocaleString();
    sheet.getRange("A1").setValue(`Last updated: ${timestamp}`);
    
    if (portfolioData.cached_at) {
      sheet.getRange("C1").setValue(`Data cached at: ${portfolioData.cached_at}`);
    }
    
    Logger.log("=== fetchSolanaPortfolio completed successfully ===");
    
  } catch (error) {
    const errorMsg = `Unexpected Error: ${error.toString()}`;
    Logger.log(`FATAL ERROR: ${errorMsg}`);
  }
}

/**
 * Fetches EVM portfolio data from the Flask API and writes it to the sheet
 */
function fetchEVMPortfolio() {
  const SHEET_NAME = "EVM_portfolio";
  
  try {
    Logger.log("=== Starting fetchEVMPortfolio ===");
    
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
    Logger.log(`Fetching portfolio for wallet: ${trimmedAddress}`);
    
    // Call the Flask API
    const url = `${API_URL}?address=${encodeURIComponent(trimmedAddress)}`;
    Logger.log(`Full API URL: ${url}`);
    
    const startTime = new Date().getTime();
    
    const response = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true,
      headers: {
        "Accept": "application/json",
        "User-Agent": "GoogleSheets/1.0",
        "ngrok-skip-browser-warning": "true"
      }
    });
    
    const endTime = new Date().getTime();
    Logger.log(`API call took ${endTime - startTime}ms`);
    
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log(`Response code: ${responseCode}`);
    
    if (responseCode !== 200) {
      const errorMsg = `API Error: ${responseCode}\n\nResponse:\n${responseText.substring(0, 1000)}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check if response is HTML
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      const errorMsg = "ERROR: Received HTML instead of JSON!\n\nVisit this URL in your browser first:\n" + url;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Parse JSON
    Logger.log("Parsing JSON response...");
    let portfolioData;
    try {
      portfolioData = JSON.parse(responseText);
      Logger.log("JSON parsed successfully");
      Logger.log(`Projects count: ${portfolioData.projects ? portfolioData.projects.length : 0}`);
    } catch (parseError) {
      const errorMsg = `JSON Parse Error: ${parseError.toString()}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    // Check for API error
    if (portfolioData.error) {
      const errorMsg = `API returned error: ${portfolioData.error}\n${portfolioData.message || ""}`;
      Logger.log(`ERROR: ${errorMsg}`);
      return;
    }
    
    if (!portfolioData.projects || portfolioData.projects.length === 0) {
      Logger.log("WARNING: No portfolio projects found");
      return;
    }
    
    Logger.log("Clearing existing data...");
    const lastRow = sheet.getLastRow();
    if (lastRow >= 3) {
      sheet.getRange(3, 1, lastRow - 2, sheet.getLastColumn()).clearContent();
    }
    
    // Write headers
    Logger.log("Writing headers...");
    const headers = ["Project", "Chain", "Total Value", "Section Type", "Category", "Token/Pool", "Balance", "USD Value"];
    sheet.getRange(2, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(2, 1, 1, headers.length).setFontWeight("bold");
    
    // Prepare data rows
    const dataRows = [];
    Logger.log("Processing projects...");
    
    for (const project of portfolioData.projects) {
      const projectName = project.project_name;
      const chain = project.chain || "unknown";
      const totalValue = project.total_value || "$0";
      
      Logger.log(`  Processing project: ${projectName} (${chain})`);
      
      if (!project.sections) continue;
      
      for (const section of project.sections) {
        const sectionType = section.section_type;
        Logger.log(`    Processing section: ${sectionType}`);
        
        if (sectionType === "Token") {
          // Process token holdings
          if (section.assets && section.assets.length > 0) {
            Logger.log(`      Found ${section.assets.length} token holdings`);
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Holdings",
                asset.token,
                asset.amount,  // Token section uses 'amount' not 'balance'
                asset.usd_value
              ]);
            }
          }
        } else if (sectionType === "Lending") {
          // Process supplied assets
          if (section.supplied && section.supplied.length > 0) {
            for (const asset of section.supplied) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Supplied",
                asset.token,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
          
          // Process borrowed assets
          if (section.borrowed && section.borrowed.length > 0) {
            for (const asset of section.borrowed) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Borrowed",
                asset.token,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
        } else if (sectionType === "Yield") {
          if (section.assets && section.assets.length > 0) {
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Yield",
                asset.pool,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
        } else if (sectionType === "Deposit") {
          if (section.assets && section.assets.length > 0) {
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Deposit",
                asset.pool,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
        } else if (sectionType === "Staked") {
          if (section.assets && section.assets.length > 0) {
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Staked",
                asset.pool,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
        } else if (sectionType === "Locked") {
          if (section.assets && section.assets.length > 0) {
            for (const asset of section.assets) {
              dataRows.push([
                projectName,
                chain,
                totalValue,
                sectionType,
                "Locked",
                asset.pool,
                asset.balance,
                asset.usd_value
              ]);
            }
          }
        }
      }
    }
    
    Logger.log(`Total data rows prepared: ${dataRows.length}`);
    
    if (dataRows.length > 0) {
      Logger.log("Writing data to sheet...");
      sheet.getRange(3, 1, dataRows.length, headers.length).setValues(dataRows);
      
      // Auto-resize columns
      for (let i = 1; i <= headers.length; i++) {
        sheet.autoResizeColumn(i);
      }
      
      Logger.log(`✓ Successfully fetched portfolio data! ${dataRows.length} rows imported.`);
    } else {
      Logger.log("WARNING: No portfolio data found");
    }
    
    // Write metadata
    const timestamp = new Date().toLocaleString();
    sheet.getRange("A1").setValue(`Last updated: ${timestamp}`);
    
    if (portfolioData.cached_at) {
      sheet.getRange("D1").setValue(`Data cached at: ${portfolioData.cached_at}`);
    }
    
    Logger.log("=== fetchEVMPortfolio completed successfully ===");
    
  } catch (error) {
    const errorMsg = `Unexpected Error: ${error.toString()}`;
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
        "ngrok-skip-browser-warning": "true"
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
                    `Solana wallets: ${healthData.solana_wallets}\n` +
                    `EVM wallets: ${healthData.evm_wallets}\n` +
                    `Last update: ${healthData.last_update || "N/A"}\n` +
                    `Scrape interval: ${healthData.scrape_interval_minutes || "N/A"} min`;
        Logger.log(msg);
      } catch (e) {
        Logger.log("Response is not valid JSON");
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