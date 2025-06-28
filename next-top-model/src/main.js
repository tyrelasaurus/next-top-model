const { invoke } = window.__TAURI__.core;

let currentPage = 'dashboard';
let teamsData = [];
let gamesData = [];
let currentGamesPage = 1;
let gamesPerPage = 50;
let gamesSortBy = 'date';
let gamesSortDirection = 'desc';
let currentTeamUid = null;
let temperatureUnit = 'celsius'; // 'celsius' or 'fahrenheit'

// Enhanced logging system for debugging
const DEBUG_LOG = [];
function debugLog(message, data = null) {
  const timestamp = new Date().toISOString();
  const logEntry = { timestamp, message, data };
  DEBUG_LOG.push(logEntry);
  console.log(`[DEBUG ${timestamp}] ${message}`, data || '');
  
  // Keep only last 100 entries
  if (DEBUG_LOG.length > 100) {
    DEBUG_LOG.shift();
  }
}

// Global debug function
window.getDebugLog = () => DEBUG_LOG;
window.clearDebugLog = () => DEBUG_LOG.length = 0;

// API functions
async function getTeams() {
  try {
    return await invoke("get_teams");
  } catch (error) {
    console.error("Error fetching teams:", error);
    return [];
  }
}

async function getGames(season = null, teamUid = null) {
  try {
    const games = await invoke("get_games", { season, team_uid: teamUid });
    // Fix game types based on date (database has incorrect classifications)
    return games.map(game => ({
      ...game,
      game_type: correctGameType(game)
    }));
  } catch (error) {
    console.error("Error fetching games:", error);
    return [];
  }
}

async function getTeamSeasonStats(season = null, teamUid = null) {
  try {
    return await invoke("get_team_season_stats", { season, team_uid: teamUid });
  } catch (error) {
    console.error("Error fetching team season stats:", error);
    return [];
  }
}

async function getTeamGameStats(gameUid = null, teamUid = null) {
  try {
    return await invoke("get_team_game_stats", { game_uid: gameUid, team_uid: teamUid });
  } catch (error) {
    console.error("Error fetching team game stats:", error);
    return [];
  }
}

async function getHistoricalMatchups(homeTeamUid, awayTeamUid) {
  try {
    // Get all games between these two teams
    const allGames = await getGames();
    return allGames.filter(game => 
      (game.home_team_uid === homeTeamUid && game.away_team_uid === awayTeamUid) ||
      (game.home_team_uid === awayTeamUid && game.away_team_uid === homeTeamUid)
    ).sort((a, b) => new Date(b.game_datetime) - new Date(a.game_datetime));
  } catch (error) {
    console.error("Error fetching historical matchups:", error);
    return [];
  }
}

function correctGameType(game) {
  if (!game.game_datetime) return game.game_type;
  
  const gameDate = new Date(game.game_datetime);
  const month = gameDate.getMonth() + 1; // JavaScript months are 0-indexed
  const year = gameDate.getFullYear();
  
  // Only correct misclassified preseason games that are marked as 'playoff' in August
  if (game.game_type === 'playoff' && month === 8) {
    console.log('Correcting August playoff game to preseason:', game.game_uid);
    return 'preseason';
  }
  
  // Correct misclassified regular season games in Sept-Dec
  if (game.game_type === 'playoff' && (month >= 9 && month <= 12)) {
    console.log('Correcting Sept-Dec playoff game to regular:', game.game_uid);
    return 'regular';
  }
  
  // FIX: Correct 2021 Week 18 games (January 2022) that are misclassified as playoff
  if (game.game_type === 'playoff' && game.season === 2021 && 
      year === 2022 && month === 1 && gameDate.getDate() <= 9) {
    console.log('Correcting 2021 Week 18 game to regular:', game.game_uid, gameDate.toISOString());
    return 'regular';
  }
  
  // Default to original type - trust the database for most games
  return game.game_type;
}

// Page rendering functions
function renderDashboard() {
  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[960px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">NFL Analytics Dashboard</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">Comprehensive analysis of NFL teams, games, and season performance.</p>
        </div>
      </div>
      
      <div class="flex flex-wrap gap-4 p-4">
        <div class="flex min-w-[158px] flex-1 flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
          <p class="text-white text-base font-medium leading-normal">Total Teams</p>
          <p class="text-white tracking-light text-2xl font-bold leading-tight" id="teams-count">32</p>
        </div>
        <div class="flex min-w-[158px] flex-1 flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
          <p class="text-white text-base font-medium leading-normal">Total Games</p>
          <p class="text-white tracking-light text-2xl font-bold leading-tight" id="games-count">-</p>
        </div>
        <div class="flex min-w-[158px] flex-1 flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
          <p class="text-white text-base font-medium leading-normal">Seasons</p>
          <p class="text-white tracking-light text-2xl font-bold leading-tight">2021-2024</p>
        </div>
      </div>

      <h2 class="text-white text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5">Quick Actions</h2>
      <div class="flex flex-wrap gap-4 p-4">
        <button class="quick-action-btn flex min-w-[200px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-6 bg-[#2e2348] text-white text-sm font-bold leading-normal" data-page="teams">
          View All Teams
        </button>
        <button class="quick-action-btn flex min-w-[200px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-6 bg-[#2e2348] text-white text-sm font-bold leading-normal" data-page="games">
          Browse Games
        </button>
        <button class="quick-action-btn flex min-w-[200px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-6 bg-[#2e2348] text-white text-sm font-bold leading-normal" data-page="standings">
          View Standings
        </button>
        <button id="debug-btn" class="flex min-w-[200px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-6 bg-[#dc2626] text-white text-sm font-bold leading-normal">
          🐛 Debug
        </button>
      </div>

      <div id="dashboard-stats-section">
        <!-- Enhanced statistics will be loaded here -->
      </div>
    </div>
  `;
  
  // Load dashboard data
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const dbTest = await invoke("test_db_connection");
    console.log('Database test result:', dbTest);
    
    const games = await getGames();
    document.getElementById('games-count').textContent = games.length;
    
    // Load initial dashboard stats
    await loadDashboardStats();
    
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
      btn.addEventListener('click', () => switchPage(btn.getAttribute('data-page')));
    });
    
    const debugBtn = document.getElementById('debug-btn');
    if (debugBtn) {
      debugBtn.addEventListener('click', showDebugInfo);
    }

  } catch (error) {
    console.error('Error loading dashboard data:', error);
    document.getElementById('games-count').textContent = 'Error';
  }
}

function renderTeams() {
  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[1200px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">NFL Teams</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">Browse all 32 NFL teams organized by conference and division.</p>
        </div>
      </div>

      <div class="flex gap-4 p-4">
        <select id="conference-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="">All Conferences</option>
          <option value="AFC">AFC</option>
          <option value="NFC">NFC</option>
        </select>
        <select id="division-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="">All Divisions</option>
          <option value="East">East</option>
          <option value="North">North</option>
          <option value="South">South</option>
          <option value="West">West</option>
        </select>
      </div>

      <div id="teams-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        <!-- Teams will be loaded here -->
      </div>
    </div>
  `;
  
  loadTeams();
  
  // Add event listeners for filters
  document.getElementById('conference-filter').addEventListener('change', filterTeams);
  document.getElementById('division-filter').addEventListener('change', filterTeams);
}

async function loadTeams() {
  try {
    console.log('Loading teams...');
    teamsData = await getTeams();
    console.log('Teams loaded:', teamsData.length);
    renderTeamsGrid(teamsData);
  } catch (error) {
    console.error('Error loading teams:', error);
    const grid = document.getElementById('teams-grid');
    grid.innerHTML = `<p class="text-red-400 text-center col-span-full">Error loading teams: ${error}</p>`;
  }
}

function renderTeamsGrid(teams) {
  const grid = document.getElementById('teams-grid');
  grid.innerHTML = teams.map(team => `
    <div class="flex flex-col gap-3 rounded-xl border border-[#423267] bg-[#2e2348] p-4">
      <div class="flex items-center gap-3">
        <div class="flex flex-col">
          <p class="text-white text-lg font-bold leading-tight">${team.city ? team.city + ' ' : ''}${team.name}</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">${team.conference} ${team.division}</p>
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <p class="text-[#a292c9] text-sm font-normal leading-normal">Stadium: ${team.stadium_name || 'N/A'}</p>
        <p class="text-[#a292c9] text-sm font-normal leading-normal">Capacity: ${team.stadium_capacity ? team.stadium_capacity.toLocaleString() : 'N/A'}</p>
      </div>
      <div class="flex gap-2">
        <button class="team-games-btn flex cursor-pointer items-center justify-center overflow-hidden rounded-lg h-8 px-4 bg-[#423267] text-white text-sm font-medium leading-normal" data-team-uid="${team.team_uid}" data-team-name="${team.name}">
          View Games
        </button>
        <button class="team-detail-btn flex cursor-pointer items-center justify-center overflow-hidden rounded-lg h-8 px-4 bg-[#6b46c1] text-white text-sm font-medium leading-normal" data-team-uid="${team.team_uid}" data-team-name="${team.name}">
          Team Details
        </button>
      </div>
    </div>
  `).join('');
  
  // Add event listeners for team games buttons
  document.querySelectorAll('.team-games-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const teamUid = btn.getAttribute('data-team-uid');
      const teamName = btn.getAttribute('data-team-name');
      viewTeamGames(teamUid, teamName);
    });
  });
  
  // Add event listeners for team detail buttons
  document.querySelectorAll('.team-detail-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const teamUid = btn.getAttribute('data-team-uid');
      const teamName = btn.getAttribute('data-team-name');
      viewTeamDetails(teamUid, teamName);
    });
  });
}

function filterTeams() {
  const conferenceFilter = document.getElementById('conference-filter').value;
  const divisionFilter = document.getElementById('division-filter').value;
  
  const filteredTeams = teamsData.filter(team => {
    return (conferenceFilter === '' || team.conference === conferenceFilter) &&
           (divisionFilter === '' || team.division === divisionFilter);
  });
  
  renderTeamsGrid(filteredTeams);
}

async function renderGames() {
  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[1200px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">NFL Games</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">Browse games by season, week, and team.</p>
        </div>
      </div>

      <div class="flex gap-4 p-4 flex-wrap">
        <select id="season-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="">All Seasons</option>
          <option value="2024">2024</option>
          <option value="2023">2023</option>
          <option value="2022">2022</option>
          <option value="2021">2021</option>
        </select>
        <select id="game-type-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="">All Game Types</option>
          <option value="preseason">Preseason</option>
          <option value="regular">Regular Season</option>
          <option value="playoff">Playoffs</option>
        </select>
        <input type="text" id="team-search" placeholder="Search team name..." class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
      </div>

      <div id="games-container" class="p-4">
        <div class="text-center text-[#a292c9]">Loading games...</div>
      </div>
    </div>
  `;
  
  // Add event listeners
  document.getElementById('season-filter').addEventListener('change', filterGames);
  document.getElementById('game-type-filter').addEventListener('change', filterGames);
  document.getElementById('team-search').addEventListener('input', filterGames);
  
  // Load games after the UI is set up
  await loadGames();
}

async function loadGames() {
  try {
    console.log('Loading games...');
    
    // Ensure teams are loaded first for team name resolution
    if (teamsData.length === 0) {
      console.log('Loading teams first for games page...');
      teamsData = await getTeams();
      console.log('Teams loaded for games:', teamsData.length);
    }
    
    gamesData = await getGames();
    console.log('Games loaded:', gamesData.length);
    console.log('Teams available for rendering:', teamsData.length);
    
    // Apply default sort (newest games first)
    gamesData = sortGames(gamesData, gamesSortBy, gamesSortDirection);
    filteredGamesData = gamesData; // Initialize filtered data
    currentGamesPage = 1; // Reset pagination
    
    // Ensure teams are loaded before rendering
    if (teamsData.length > 0) {
      renderGamesTable(gamesData);
    } else {
      console.error('Teams not loaded properly');
      const container = document.getElementById('games-container');
      container.innerHTML = `<p class="text-red-400 text-center">Error: Teams data not loaded</p>`;
    }
  } catch (error) {
    console.error('Error loading games:', error);
    const container = document.getElementById('games-container');
    container.innerHTML = `<p class="text-red-400 text-center">Error loading games: ${error}</p>`;
  }
}

function renderGamesTable(games) {
  debugLog('renderGamesTable called', { 
    gamesCount: games.length, 
    teamsDataLength: teamsData.length,
    currentPage: currentPage 
  });
  
  const container = document.getElementById('games-container');
  if (games.length === 0) {
    debugLog('renderGamesTable: No games to render');
    container.innerHTML = '<p class="text-[#a292c9] text-center">No games found</p>';
    return;
  }
  
  const totalPages = Math.ceil(games.length / gamesPerPage);
  const startIndex = (currentGamesPage - 1) * gamesPerPage;
  const endIndex = startIndex + gamesPerPage;
  const currentGames = games.slice(startIndex, endIndex);
  
  container.innerHTML = `
    <div class="flex overflow-hidden rounded-xl border border-[#423267] bg-[#161122]">
      <table class="flex-1">
        <thead>
          <tr class="bg-[#211933]">
            <th class="sortable-header px-4 py-3 text-left text-white text-sm font-medium leading-normal cursor-pointer hover:bg-[#2e2348]" data-sort="date">
              Date ${getSortIcon('date')}
            </th>
            <th class="sortable-header px-4 py-3 text-left text-white text-sm font-medium leading-normal cursor-pointer hover:bg-[#2e2348]" data-sort="matchup">
              Matchup ${getSortIcon('matchup')}
            </th>
            <th class="sortable-header px-4 py-3 text-left text-white text-sm font-medium leading-normal cursor-pointer hover:bg-[#2e2348]" data-sort="score">
              Score ${getSortIcon('score')}
            </th>
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Type</th>
            <th class="sortable-header px-4 py-3 text-left text-white text-sm font-medium leading-normal cursor-pointer hover:bg-[#2e2348]" data-sort="season">
              Season ${getSortIcon('season')}
            </th>
          </tr>
        </thead>
        <tbody>
          ${currentGames.map((game, index) => {
            const awayTeam = getTeamName(game.away_team_uid);
            const homeTeam = getTeamName(game.home_team_uid);
            
            // Log first few games for debugging
            if (index < 3) {
              debugLog('renderGamesTable: Rendering game row', {
                index,
                gameUid: game.game_uid,
                awayTeam,
                homeTeam,
                awayTeamUid: game.away_team_uid,
                homeTeamUid: game.home_team_uid
              });
            }
            
            return `<tr class="border-t border-t-[#423267] hover:bg-[#2e2348] cursor-pointer game-row" data-game-uid="${game.game_uid}">
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${game.game_datetime ? new Date(game.game_datetime).toLocaleDateString() : 'TBD'}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${awayTeam} @ ${homeTeam}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${game.away_score !== null && game.home_score !== null ? 
                  `${game.away_score}-${game.home_score}${game.overtime ? ' (OT)' : ''}` : 
                  'Not played'}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${getGameTypeDisplay(game.game_type)}${game.week ? ` (Week ${Math.floor(game.week)})` : ''}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${game.season}
              </td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>
    
    <!-- Pagination -->
    <div class="flex items-center justify-between mt-4">
      <p class="text-[#a292c9] text-sm">
        Showing ${startIndex + 1}-${Math.min(endIndex, games.length)} of ${games.length} games
      </p>
      <div class="flex gap-2">
        <button 
          class="prev-btn px-3 py-1 rounded bg-[#2e2348] text-white text-sm ${currentGamesPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#423267]'}"
          ${currentGamesPage === 1 ? 'disabled' : ''}
        >
          Previous
        </button>
        <span class="px-3 py-1 text-white text-sm">
          Page ${currentGamesPage} of ${totalPages}
        </span>
        <button 
          class="next-btn px-3 py-1 rounded bg-[#2e2348] text-white text-sm ${currentGamesPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#423267]'}"
          ${currentGamesPage === totalPages ? 'disabled' : ''}
        >
          Next
        </button>
      </div>
    </div>
  `;
  
  // Simple click handler approach using event delegation
  const tableBody = document.querySelector('tbody');
  debugLog('renderGamesTable: Setting up click handlers', {
    tableBodyFound: !!tableBody,
    tableBodyTag: tableBody ? tableBody.tagName : 'none',
    gameRowsInDOM: document.querySelectorAll('.game-row').length
  });
  
  if (tableBody) {
    // Remove existing click handler
    tableBody.removeEventListener('click', handleTableClick);
    // Add new click handler
    tableBody.addEventListener('click', handleTableClick);
    
    debugLog('renderGamesTable: Click handler added to table body');
    
    // Test that game rows have the correct attributes
    setTimeout(() => {
      const gameRows = document.querySelectorAll('.game-row');
      debugLog('renderGamesTable: Post-render game rows check', {
        totalGameRows: gameRows.length,
        firstGameRowUid: gameRows[0] ? gameRows[0].getAttribute('data-game-uid') : 'none',
        firstGameRowClasses: gameRows[0] ? gameRows[0].className : 'none'
      });
    }, 100);
  } else {
    debugLog('renderGamesTable: ERROR - No table body found for click handler');
  }
  
  // Add sortable header event listeners
  document.querySelectorAll('.sortable-header').forEach(header => {
    header.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent bubbling to game row clicks
      const sortColumn = header.getAttribute('data-sort');
      handleSort(sortColumn);
    });
  });
  
  // Add pagination event listeners
  const prevBtn = document.querySelector('.prev-btn');
  const nextBtn = document.querySelector('.next-btn');
  
  if (prevBtn && !prevBtn.disabled) {
    prevBtn.addEventListener('click', () => {
      changeGamesPage(currentGamesPage - 1);
    });
  }
  
  if (nextBtn && !nextBtn.disabled) {
    nextBtn.addEventListener('click', () => {
      changeGamesPage(currentGamesPage + 1);
    });
  }
}

function changeGamesPage(newPage) {
  const currentData = filteredGamesData.length > 0 ? filteredGamesData : gamesData;
  const totalPages = Math.ceil(currentData.length / gamesPerPage);
  if (newPage >= 1 && newPage <= totalPages) {
    currentGamesPage = newPage;
    renderGamesTable(currentData);
  }
}

function getTeamName(teamUid) {
  debugLog('getTeamName called', { teamUid, teamsDataLength: teamsData.length });
  
  if (!teamUid) {
    debugLog('getTeamName: No teamUid provided');
    return 'No UID';
  }
  
  if (teamsData.length === 0) {
    debugLog('getTeamName: No teams data loaded');
    return 'No Teams Data';
  }
  
  const team = teamsData.find(t => t.team_uid === teamUid);
  
  if (!team) {
    debugLog('getTeamName: Team not found', { 
      teamUid, 
      availableTeams: teamsData.length,
      sampleTeamUIDs: teamsData.slice(0, 3).map(t => t.team_uid)
    });
    return 'Unknown';
  }
  
  const result = team.abbreviation || team.name;
  debugLog('getTeamName: Success', { teamUid, result });
  return result;
}

function getGameTypeDisplay(gameType) {
  switch(gameType) {
    case 'preseason': return 'Preseason';
    case 'regular': return 'Regular Season';
    case 'playoff': return 'Playoffs';
    default: return gameType || 'N/A';
  }
}

function getSortIcon(column) {
  if (gamesSortBy !== column) {
    return '<span class="text-[#a292c9] ml-1">↕</span>';
  }
  return gamesSortDirection === 'asc' ? 
    '<span class="text-white ml-1">↑</span>' : 
    '<span class="text-white ml-1">↓</span>';
}

function sortGames(games, sortBy, direction) {
  return [...games].sort((a, b) => {
    let aVal, bVal;
    
    switch(sortBy) {
      case 'date':
        aVal = new Date(a.game_datetime || '1900-01-01');
        bVal = new Date(b.game_datetime || '1900-01-01');
        break;
      case 'matchup':
        aVal = `${getTeamName(a.away_team_uid)} @ ${getTeamName(a.home_team_uid)}`;
        bVal = `${getTeamName(b.away_team_uid)} @ ${getTeamName(b.home_team_uid)}`;
        break;
      case 'score':
        // Sort by total points scored (home + away)
        aVal = (a.home_score || 0) + (a.away_score || 0);
        bVal = (b.home_score || 0) + (b.away_score || 0);
        break;
      case 'season':
        aVal = a.season;
        bVal = b.season;
        break;
      default:
        return 0;
    }
    
    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

function handleSort(column) {
  if (gamesSortBy === column) {
    // Toggle direction if same column
    gamesSortDirection = gamesSortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    // New column, default to ascending except date (descending for newest first)
    gamesSortBy = column;
    gamesSortDirection = column === 'date' ? 'desc' : 'asc';
  }
  
  // Sort the current data and re-render
  const currentData = filteredGamesData.length > 0 ? filteredGamesData : gamesData;
  const sortedData = sortGames(currentData, gamesSortBy, gamesSortDirection);
  
  // Update the data arrays
  if (filteredGamesData.length > 0) {
    filteredGamesData = sortedData;
  } else {
    gamesData = sortedData;
  }
  
  // Reset to first page and re-render
  currentGamesPage = 1;
  renderGamesTable(sortedData);
}

let filteredGamesData = [];

function filterGames() {
  const seasonFilter = document.getElementById('season-filter').value;
  const gameTypeFilter = document.getElementById('game-type-filter').value;
  const teamSearch = document.getElementById('team-search').value.toLowerCase();
  
  filteredGamesData = gamesData.filter(game => {
    const seasonMatch = seasonFilter === '' || game.season.toString() === seasonFilter;
    const typeMatch = gameTypeFilter === '' || game.game_type === gameTypeFilter;
    const teamMatch = teamSearch === '' || 
      getTeamName(game.home_team_uid).toLowerCase().includes(teamSearch) ||
      getTeamName(game.away_team_uid).toLowerCase().includes(teamSearch);
    
    return seasonMatch && typeMatch && teamMatch;
  });
  
  // Apply current sort to filtered data
  filteredGamesData = sortGames(filteredGamesData, gamesSortBy, gamesSortDirection);
  
  // Reset to first page when filtering
  currentGamesPage = 1;
  renderGamesTable(filteredGamesData);
}

function renderStandings() {
  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[1200px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">NFL Standings</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">Team standings and conference rankings.</p>
        </div>
      </div>

      <div class="flex gap-4 p-4">
        <select id="standings-season" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="2024">2024 Season</option>
          <option value="2023">2023 Season</option>
          <option value="2022">2022 Season</option>
          <option value="2021">2021 Season</option>
        </select>
      </div>

      <div id="standings-content" class="p-4">
        <!-- Standings will be loaded here -->
      </div>
    </div>
  `;
  
  loadStandings();
  document.getElementById('standings-season').addEventListener('change', loadStandings);
}

async function loadStandings() {
  try {
    const season = document.getElementById('standings-season').value;
    console.log('Loading standings for season:', season);
    
    // Ensure teams are loaded first
    if (teamsData.length === 0) {
      console.log('Loading teams for standings...');
      teamsData = await getTeams();
    }
    
    const seasonGames = await getGames(parseInt(season));
    console.log('Season games loaded:', seasonGames.length);
    const standings = calculateStandings(seasonGames);
    renderStandingsTable(standings);
  } catch (error) {
    console.error('Error loading standings:', error);
    const container = document.getElementById('standings-content');
    container.innerHTML = `<p class="text-red-400 text-center">Error loading standings: ${error}</p>`;
  }
}

function calculateStandings(games) {
  debugLog('calculateStandings called', { 
    totalGames: games.length, 
    currentSeason: document.getElementById('season-filter')?.value || 'all'
  });
  
  console.log('Calculating standings with', games.length, 'games');
  
  // Debug game types before correction
  const gameTypeCount = {};
  games.forEach(game => {
    const type = game.game_type || 'null';
    gameTypeCount[type] = (gameTypeCount[type] || 0) + 1;
  });
  debugLog('calculateStandings: Game types before correction', gameTypeCount);
  console.log('Game types before correction:', gameTypeCount);
  
  const teamStats = {};
  
  // Initialize stats for all teams
  teamsData.forEach(team => {
    teamStats[team.team_uid] = {
      team: team,
      wins: 0,
      losses: 0,
      pointsFor: 0,
      pointsAgainst: 0
    };
  });
  
  console.log('Initialized stats for', Object.keys(teamStats).length, 'teams');
  
  let regularSeasonGames = 0;
  let processedGames = 0;
  let gamesWithScores = 0;
  const teamGameCounts = {}; // Track games per team for debugging
  
  // Calculate stats from games
  games.forEach(game => {
    processedGames++;
    
    // Check if game has scores
    if (game.home_score !== null && game.away_score !== null) {
      gamesWithScores++;
    }
    
    // Check for regular season games (note: database uses 'regular', not 'Regular Season')
    if (game.home_score !== null && game.away_score !== null && game.game_type === 'regular') {
      regularSeasonGames++;
      
      // Count games per team for debugging
      teamGameCounts[game.home_team_uid] = (teamGameCounts[game.home_team_uid] || 0) + 1;
      teamGameCounts[game.away_team_uid] = (teamGameCounts[game.away_team_uid] || 0) + 1;
      
      const homeWin = game.home_score > game.away_score;
      
      debugLog('calculateStandings: Processing regular season game', {
        gameUid: game.game_uid,
        homeTeam: game.home_team_uid,
        awayTeam: game.away_team_uid,
        homeScore: game.home_score,
        awayScore: game.away_score,
        homeWin,
        season: game.season
      });
      
      if (teamStats[game.home_team_uid]) {
        teamStats[game.home_team_uid].pointsFor += game.home_score;
        teamStats[game.home_team_uid].pointsAgainst += game.away_score;
        if (homeWin) {
          teamStats[game.home_team_uid].wins++;
        } else {
          teamStats[game.home_team_uid].losses++;
        }
      }
      
      if (teamStats[game.away_team_uid]) {
        teamStats[game.away_team_uid].pointsFor += game.away_score;
        teamStats[game.away_team_uid].pointsAgainst += game.home_score;
        if (!homeWin) {
          teamStats[game.away_team_uid].wins++;
        } else {
          teamStats[game.away_team_uid].losses++;
        }
      }
    }
  });
  
  console.log('Processed', processedGames, 'total games');
  console.log('Games with scores:', gamesWithScores);
  console.log('Regular season games counted:', regularSeasonGames);
  
  // Enhanced debugging for game count issue
  const gameCountValues = Object.values(teamGameCounts);
  const avgGamesPerTeam = gameCountValues.length > 0 ? 
    gameCountValues.reduce((sum, count) => sum + count, 0) / gameCountValues.length : 0;
  
  debugLog('calculateStandings: Final game count analysis', {
    regularSeasonGames,
    teamsWithGames: gameCountValues.length,
    avgGamesPerTeam: avgGamesPerTeam.toFixed(1),
    expectedGames: 17,
    gameCountRange: {
      min: Math.min(...gameCountValues),
      max: Math.max(...gameCountValues)
    },
    sampleTeamCounts: Object.entries(teamGameCounts).slice(0, 5)
  });
  
  // Debug: Check a few team totals
  const sampleTeams = Object.values(teamStats).slice(0, 3);
  sampleTeams.forEach(team => {
    const totalGames = team.wins + team.losses;
    console.log(`${team.team.abbreviation}: ${team.wins}-${team.losses} (${totalGames} total games)`);
    debugLog('calculateStandings: Sample team record', {
      team: team.team.abbreviation,
      wins: team.wins,
      losses: team.losses,
      totalGames,
      expectedGames: 17
    });
  });
  
  // Group by conference and division
  const standings = {
    AFC: { East: [], North: [], South: [], West: [] },
    NFC: { East: [], North: [], South: [], West: [] }
  };
  
  Object.values(teamStats).forEach(stat => {
    if (stat.team.conference && stat.team.division) {
      standings[stat.team.conference][stat.team.division].push(stat);
    }
  });
  
  // Sort each division by wins (descending), then losses (ascending)
  Object.keys(standings).forEach(conference => {
    Object.keys(standings[conference]).forEach(division => {
      standings[conference][division].sort((a, b) => {
        if (b.wins !== a.wins) return b.wins - a.wins;
        return a.losses - b.losses;
      });
    });
  });
  
  console.log('Standings calculated for', Object.keys(standings).length, 'conferences');
  return standings;
}

function renderStandingsTable(standings) {
  const container = document.getElementById('standings-content');
  const season = document.getElementById('standings-season').value;
  
  container.innerHTML = Object.keys(standings).map(conference => `
    <div class="mb-8">
      <h3 class="text-white text-xl font-bold mb-4">${conference} Conference</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        ${Object.keys(standings[conference]).map(division => `
          <div>
            <h4 class="text-white text-lg font-semibold mb-2">${conference} ${division}</h4>
            <div class="rounded-lg border border-[#423267] bg-[#2e2348] overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="bg-[#211933]">
                    <th class="px-3 py-2 text-left text-white text-sm font-medium">Team</th>
                    <th class="px-3 py-2 text-center text-white text-sm font-medium">W</th>
                    <th class="px-3 py-2 text-center text-white text-sm font-medium">L</th>
                    <th class="px-3 py-2 text-center text-white text-sm font-medium">PF</th>
                    <th class="px-3 py-2 text-center text-white text-sm font-medium">PA</th>
                  </tr>
                </thead>
                <tbody>
                  ${standings[conference][division].map(stat => `
                    <tr class="border-t border-[#423267]">
                      <td 
                        class="px-3 py-2 text-white text-sm cursor-pointer hover:text-blue-400 team-schedule-link"
                        data-team-uid="${stat.team.team_uid}"
                        data-team-name="${stat.team.name}"
                        data-season="${season}"
                      >
                        ${stat.team.city} ${stat.team.name}
                      </td>
                      <td class="px-3 py-2 text-center text-[#a292c9] text-sm">${stat.wins}</td>
                      <td class="px-3 py-2 text-center text-[#a292c9] text-sm">${stat.losses}</td>
                      <td class="px-3 py-2 text-center text-[#a292c9] text-sm">${stat.pointsFor}</td>
                      <td class="px-3 py-2 text-center text-[#a292c9] text-sm">${stat.pointsAgainst}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
  
  // Add event listeners for team schedule links
  document.querySelectorAll('.team-schedule-link').forEach(link => {
    link.addEventListener('click', (e) => {
      const teamUid = e.target.dataset.teamUid;
      const teamName = e.target.dataset.teamName;
      const season = e.target.dataset.season;
      viewTeamGames(teamUid, teamName, season);
    });
  });
}

// Navigation functions
async function switchPage(page) {
  currentPage = page;
  
  // Update navigation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('text-blue-400');
    if (link.dataset.page === page) {
      link.classList.add('text-blue-400');
    }
  });
  
  // Render page
  switch (page) {
    case 'dashboard':
      renderDashboard();
      break;
    case 'teams':
      renderTeams();
      break;
    case 'games':
      await renderGames();
      break;
    case 'standings':
      renderStandings();
      break;
    case 'settings':
      renderSettings();
      break;
  }
}

async function viewTeamGames(teamUid, teamName, season = null) {
  await switchPage('games');
  // Wait for the games page to load, then filter
  setTimeout(() => {
    const teamSearch = document.getElementById('team-search');
    const seasonFilter = document.getElementById('season-filter');
    
    if (teamSearch && seasonFilter) {
      // Find the team to get its abbreviation or name
      const team = teamsData.find(t => t.team_uid === teamUid);
      const searchTerm = team ? (team.abbreviation || team.name) : teamName;
      teamSearch.value = searchTerm;
      
      // Set the season filter if provided
      if (season) {
        seasonFilter.value = season;
      }
      
      // Trigger the filtering logic
      filterGames();
    }
  }, 100);
}

function viewTeamDetails(teamUid, teamName) {
  currentPage = 'team-detail';
  currentTeamUid = teamUid;
  renderTeamDetails(teamUid);
}

async function viewGameDetails(gameUid) {
  console.log('viewGameDetails called with gameUid:', gameUid);
  currentPage = 'game-detail';
  
  // Ensure teams are loaded for game details
  if (teamsData.length === 0) {
    console.log('Loading teams for game details...');
    teamsData = await getTeams();
    console.log('Teams loaded:', teamsData.length);
  }
  
  console.log('Calling renderGameDetails...');
  renderGameDetails(gameUid);
}

async function renderTeamDetails(teamUid) {
  const team = teamsData.find(t => t.team_uid === teamUid);
  if (!team) {
    console.error('Team not found:', teamUid);
    return;
  }

  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[1200px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <div class="flex items-center gap-3">
            <button id="back-to-teams" class="flex cursor-pointer items-center justify-center rounded-lg h-8 px-3 bg-[#2e2348] text-white text-sm font-medium hover:bg-[#423267]">
              ← Back to Teams
            </button>
          </div>
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">${team.city} ${team.name}</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">${team.conference} ${team.division} • ${team.stadium_name}</p>
        </div>
      </div>

      <div class="flex gap-4 p-4">
        <select id="team-season-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
          <option value="">All Seasons</option>
          <option value="2024">2024 Season</option>
          <option value="2023">2023 Season</option>
          <option value="2022">2022 Season</option>
          <option value="2021">2021 Season</option>
        </select>
      </div>

      <div id="team-stats-content" class="p-4">
        <div class="text-center text-[#a292c9]">Loading team statistics...</div>
      </div>
    </div>
  `;

  // Add back button listener
  document.getElementById('back-to-teams').addEventListener('click', () => {
    switchPage('teams');
  });

  // Add season filter listener
  document.getElementById('team-season-filter').addEventListener('change', () => {
    loadTeamDetails(teamUid);
  });

  // Load initial data
  loadTeamDetails(teamUid);
}


let teamDetailsState = {
  gameStats: [],
  sort: {
    column: 'date',
    direction: 'desc'
  },
  pagination: {
    currentPage: 1,
    gamesPerPage: 10
  }
};

async function loadTeamDetails(teamUid) {
  try {
    const team = teamsData.find(t => t.team_uid === teamUid);
    const seasonFilter = document.getElementById('team-season-filter')?.value;
    const season = seasonFilter ? parseInt(seasonFilter) : null;

    console.log(`Loading details for team ${teamUid} and season ${season}`);

    // 1. Fetch all necessary data unfiltered
    const allTeamSeasonStats = await getTeamSeasonStats(null, teamUid);
    const allTeamGames = await getGames(null, teamUid);
    const allTeamGameStats = await getTeamGameStats(null, teamUid);

    // 2. Filter data based on season selection
    const filteredSeasonStats = season ? allTeamSeasonStats.filter(s => s.season === season) : allTeamSeasonStats;
    const filteredGames = season ? allTeamGames.filter(g => g.season === season) : allTeamGames;

    // 3. Enrich game data with opponent and detailed stats
    const enrichedGames = filteredGames.map(game => {
      const gameStats = allTeamGameStats.find(gs => gs.game_uid === game.game_uid && gs.team_uid === teamUid);
      const isHome = game.home_team_uid === teamUid;
      const opponent_team_uid = isHome ? game.away_team_uid : game.home_team_uid;
      const result = game.home_score === null ? 'TBD' : (isHome ? (game.home_score > game.away_score ? 'W' : 'L') : (game.away_score > game.home_score ? 'W' : 'L'));
      
      return {
        ...game,
        ...gameStats,
        opponent_team_uid,
        is_home_team: isHome,
        result
      };
    }).sort((a, b) => new Date(b.game_datetime) - new Date(a.game_datetime)); // Default sort by date desc

    // 4. Update state
    teamDetailsState.gameStats = enrichedGames;
    teamDetailsState.pagination.currentPage = 1; // Reset page on new data load

    // 5. Render everything
    renderTeamStatsContent(team, filteredSeasonStats, enrichedGames);

  } catch (error) {
    console.error('Error loading team details:', error);
    const container = document.getElementById('team-stats-content');
    container.innerHTML = `<p class="text-red-400 text-center">Error loading team details: ${error}</p>`;
  }
}

function renderTeamStatsContent(team, seasonStats, gameStats) {
  const container = document.getElementById('team-stats-content');
  
  const validSeasonStats = seasonStats.filter(stat => (stat.wins > 0 || stat.losses > 0 || stat.ties > 0));

  // Paginate game stats
  const { currentPage, gamesPerPage } = teamDetailsState.pagination;
  const totalPages = Math.ceil(gameStats.length / gamesPerPage);
  const paginatedGames = gameStats.slice((currentPage - 1) * gamesPerPage, currentPage * gamesPerPage);

  container.innerHTML = `
    <!-- Season Statistics -->
    <div class="mb-8">
      <h3 class="text-white text-xl font-bold mb-4">Season Records</h3>
      ${validSeasonStats.length > 0 ? `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          ${validSeasonStats.map(stat => `
            <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
              <p class="text-white text-lg font-semibold">${stat.season} Season</p>
              <p class="text-[#a292c9] text-sm">${stat.wins}-${stat.losses}${stat.ties > 0 ? `-${stat.ties}`: ''}</p>
            </div>
          `).join('')}
        </div>
      ` : `<p class="text-[#a292c9]">No season records available for this selection.</p>`}
    </div>

    <!-- Game Performance -->
    <div class="mb-8">
      <h3 class="text-white text-xl font-bold mb-4">Game Performance</h3>
      <div id="team-games-table-container"></div>
    </div>

    <!-- Performance Averages -->
    <div class="mb-8">
        <h3 class="text-white text-xl font-bold mb-4">Averages (Filtered Games)</h3>
        ${gameStats.length > 0 ? `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4 text-center">
            <p class="text-[#a292c9] text-sm mb-1">Avg Total Yards</p>
            <p class="text-white text-xl font-bold">${calculateTeamAverage(gameStats, 'total_yards')}</p>
          </div>
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4 text-center">
            <p class="text-[#a292c9] text-sm mb-1">Avg Passing</p>
            <p class="text-white text-xl font-bold">${calculateTeamAverage(gameStats, 'passing_yards')}</p>
          </div>
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4 text-center">
            <p class="text-[#a292c9] text-sm mb-1">Avg Rushing</p>
            <p class="text-white text-xl font-bold">${calculateTeamAverage(gameStats, 'rushing_yards')}</p>
          </div>
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4 text-center">
            <p class="text-[#a292c9] text-sm mb-1">Avg Turnovers</p>
            <p class="text-white text-xl font-bold">${calculateTeamAverage(gameStats, 'turnovers')}</p>
          </div>
        </div>
        ` : `<p class="text-[#a292c9]">No game data to calculate averages.</p>`}
    </div>
  `;
  
  renderTeamGamesTable();
}

function renderTeamGamesTable() {
    const container = document.getElementById('team-games-table-container');
    const { gameStats, pagination, sort } = teamDetailsState;
    const { currentPage, gamesPerPage } = pagination;

    // 1. Sort the data
    const sortedStats = [...gameStats].sort((a, b) => {
        const aVal = a[sort.column] || 0;
        const bVal = b[sort.column] || 0;
        if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
        return 0;
    });

    // 2. Paginate the sorted data
    const totalPages = Math.ceil(sortedStats.length / gamesPerPage);
    const paginatedGames = sortedStats.slice((currentPage - 1) * gamesPerPage, currentPage * gamesPerPage);

    if (paginatedGames.length === 0) {
        container.innerHTML = `<p class="text-[#a292c9]">No game performance data available for this selection.</p>`;
        return;
    }

    container.innerHTML = `
        <div class="rounded-xl border border-[#423267] bg-[#161122] overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="bg-[#211933]">
                <th class="px-4 py-3 text-left text-white text-sm font-medium">Opponent</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Result</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              ${paginatedGames.map(game => `
                <tr class="border-t border-[#423267] hover:bg-[#2e2348] cursor-pointer" onclick="viewGameDetails('${game.game_uid}')">
                  <td class="px-4 py-3 text-[#a292c9] text-sm">${game.is_home_team ? '' : '@'} ${getTeamName(game.opponent_team_uid)}</td>
                  <td class="px-4 py-3 text-center text-white text-sm font-medium">${game.result}</td>
                  <td class="px-4 py-3 text-center text-white text-sm">${game.home_score !== null ? `${game.away_score} - ${game.home_score}` : 'N/A'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <!-- Pagination -->
        <div class="flex items-center justify-between mt-4">
          <p class="text-[#a292c9] text-sm">
            Showing ${((currentPage - 1) * gamesPerPage) + 1}-${Math.min(currentPage * gamesPerPage, gameStats.length)} of ${gameStats.length} games
          </p>
          <div class="flex gap-2">
            <button class="team-games-prev-btn px-3 py-1 rounded bg-[#2e2348] text-white text-sm ${currentPage === 1 ? 'opacity-50' : 'hover:bg-[#423267]'}" ${currentPage === 1 ? 'disabled' : ''}>
              Previous
            </button>
            <span class="px-3 py-1 text-white text-sm">Page ${currentPage} of ${totalPages}</span>
            <button class="team-games-next-btn px-3 py-1 rounded bg-[#2e2348] text-white text-sm ${currentPage === totalPages ? 'opacity-50' : 'hover:bg-[#423267]'}" ${currentPage === totalPages ? 'disabled' : ''}>
              Next
            </button>
          </div>
        </div>
    `;

    // Add pagination event listeners
    document.querySelector('.team-games-prev-btn').addEventListener('click', () => {
        teamDetailsState.pagination.currentPage--;
        renderTeamGamesTable();
    });
    document.querySelector('.team-games-next-btn').addEventListener('click', () => {
        teamDetailsState.pagination.currentPage++;
        renderTeamGamesTable();
    });
}

function calculateTeamAverage(stats, field) {
    const validStats = stats.filter(stat => stat[field] !== null && stat[field] !== undefined);
    if (validStats.length === 0) return 'N/A';
    const total = validStats.reduce((sum, stat) => sum + stat[field], 0);
    return (total / validStats.length).toFixed(1);
}


function calculateAverage(stats, field) {
  const validStats = stats.filter(stat => stat[field] !== null && stat[field] !== undefined);
  if (validStats.length === 0) return '-';
  
  const total = validStats.reduce((sum, stat) => sum + stat[field], 0);
  return Math.round(total / validStats.length);
}

// Global function for handling game row clicks (backup method)
window.handleGameRowClick = function(gameUid) {
  console.log('handleGameRowClick called with:', gameUid);
  viewGameDetails(gameUid);
};

// Make viewGameDetails globally accessible  
window.viewGameDetails = viewGameDetails;

// Table click handler for game rows
function handleTableClick(e) {
  debugLog('handleTableClick called', {
    target: e.target.tagName,
    targetClass: e.target.className,
    eventType: e.type
  });
  
  const row = e.target.closest('.game-row');
  debugLog('handleTableClick: Found row', { 
    rowFound: !!row,
    rowClass: row ? row.className : 'none'
  });
  
  if (row) {
    const gameUid = row.getAttribute('data-game-uid');
    debugLog('handleTableClick: Game UID from row', { 
      gameUid,
      allAttributes: row.getAttributeNames()
    });
    
    if (gameUid) {
      debugLog('handleTableClick: Calling viewGameDetails', { gameUid });
      console.log('Table click detected for game:', gameUid);
      viewGameDetails(gameUid);
    } else {
      debugLog('handleTableClick: No game UID found on row');
    }
  } else {
    debugLog('handleTableClick: No game row found in click target');
  }
}

// Debug function to show current app state
function showDebugInfo() {
  console.log('=== COMPREHENSIVE DEBUG INFO ===');
  
  // Basic data loading status
  const basicInfo = {
    teamsLoaded: teamsData.length,
    gamesLoaded: gamesData.length,
    currentPage: currentPage,
    sampleTeam: teamsData[0],
    sampleGame: gamesData[0]
  };
  
  console.log('BASIC INFO:', basicInfo);
  
  // Test Bug #1: Team name resolution
  console.log('\n=== BUG #1: TEAM NAME RESOLUTION TEST ===');
  if (gamesData.length > 0) {
    const testGames = gamesData.slice(0, 5);
    testGames.forEach((game, i) => {
      const homeTeam = getTeamName(game.home_team_uid);
      const awayTeam = getTeamName(game.away_team_uid);
      console.log(`Game ${i + 1}: ${game.game_uid}`);
      console.log(`  Teams: ${awayTeam} @ ${homeTeam}`);
      console.log(`  UIDs: ${game.away_team_uid} @ ${game.home_team_uid}`);
      console.log(`  Unknown count: ${(awayTeam === 'Unknown' ? 1 : 0) + (homeTeam === 'Unknown' ? 1 : 0)}`);
    });
  }
  
  // Test Bug #2: Click handler status
  console.log('\n=== BUG #2: CLICK HANDLER TEST ===');
  const gameRows = document.querySelectorAll('.game-row');
  const tableBody = document.querySelector('tbody');
  console.log('Game rows found:', gameRows.length);
  console.log('Table body found:', !!tableBody);
  console.log('First game row UID:', gameRows[0] ? gameRows[0].getAttribute('data-game-uid') : 'none');
  console.log('Event listeners on tbody:', tableBody ? 'yes (but count unknown)' : 'no');
  
  // Test Bug #3: Standings calculation
  console.log('\n=== BUG #3: STANDINGS CALCULATION TEST ===');
  if (gamesData.length > 0) {
    const season2024 = gamesData.filter(g => g.season === 2024);
    const regularSeason = season2024.filter(g => g.game_type === 'regular' && g.home_score !== null);
    const teamGameCount = {};
    
    regularSeason.forEach(game => {
      teamGameCount[game.home_team_uid] = (teamGameCount[game.home_team_uid] || 0) + 1;
      teamGameCount[game.away_team_uid] = (teamGameCount[game.away_team_uid] || 0) + 1;
    });
    
    const gameCounts = Object.values(teamGameCount);
    const avgGames = gameCounts.length > 0 ? gameCounts.reduce((sum, count) => sum + count, 0) / gameCounts.length : 0;
    
    console.log('2024 total games:', season2024.length);
    console.log('2024 regular season with scores:', regularSeason.length);
    console.log('Average games per team:', avgGames.toFixed(1));
    console.log('Expected games per team: 17');
    console.log('Game count range:', gameCounts.length > 0 ? `${Math.min(...gameCounts)} - ${Math.max(...gameCounts)}` : 'none');
  }
  
  // Debug log history
  console.log('\n=== DEBUG LOG HISTORY (Last 20 entries) ===');
  const recentLogs = DEBUG_LOG.slice(-20);
  recentLogs.forEach(log => {
    console.log(`[${log.timestamp}] ${log.message}`, log.data || '');
  });
  
  console.log('\n=== END DEBUG INFO ===');
  
  // Show summary alert
  const summary = `🐛 NFL App Debug Summary:
• Teams loaded: ${basicInfo.teamsLoaded}
• Games loaded: ${basicInfo.gamesLoaded}
• Current page: ${basicInfo.currentPage}
• Game rows in DOM: ${document.querySelectorAll('.game-row').length}
• Debug logs: ${DEBUG_LOG.length}

📋 Check console for comprehensive bug analysis.
💾 Debug logs saved to DEBUG_LOG array.`;
  
  alert(summary);
  
  // Make debug data globally accessible
  window.NFL_DEBUG_INFO = {
    basicInfo,
    teamsData,
    gamesData,
    debugLog: DEBUG_LOG,
    gameRowsCount: document.querySelectorAll('.game-row').length,
    tableBodyExists: !!document.querySelector('tbody')
  };
  
  console.log('Debug info saved to window.NFL_DEBUG_INFO');
}

async function loadDashboardStats() {
  try {
    const season = document.getElementById('dashboard-season-filter')?.value || '2024';
    console.log('loadDashboardStats: Loading data for season', season);
    
    // Load season stats for all teams
    let seasonStats = await getTeamSeasonStats(parseInt(season), null);
    console.log(`Dashboard season stats loaded for ${season}:`, seasonStats.length);
    
    // Check if the data is empty (all wins/losses are 0)
    const hasValidData = seasonStats.length > 0 && 
      seasonStats.some(stat => (stat.wins || 0) > 0 || (stat.losses || 0) > 0);
    
    console.log(`Season ${season} has valid team_season_stats data:`, hasValidData);
    
    // If no team_season_stats found OR data is empty (all zeros), calculate from games data
    if (seasonStats.length === 0 || !hasValidData) {
      console.log(`No valid team_season_stats found for ${season}, calculating from games data...`);
      seasonStats = await calculateSeasonStatsFromGames(parseInt(season));
      console.log(`Calculated season stats for ${season}:`, seasonStats.length);
    }
    
    if (seasonStats.length > 0) {
      renderDashboardStats(seasonStats, season);
    } else {
      // Render an empty state if no stats are found
      const statsSection = document.getElementById('dashboard-stats-section');
      statsSection.innerHTML = `
        <div class="flex justify-between items-center px-4 pb-3 pt-5">
          <h2 class="text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">Season Insights</h2>
          <select id="dashboard-season-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
            <option value="2024">2024 Season</option>
            <option value="2023">2023 Season</option>
            <option value="2022">2022 Season</option>
            <option value="2021">2021 Season</option>
          </select>
        </div>
        <p class="p-4 text-[#a292c9]">No statistics found for the ${season} season.</p>
      `;
      // Set the dropdown to the selected season and attach listener
      const filterDropdown = document.getElementById('dashboard-season-filter');
      filterDropdown.value = season;
      attachDashboardSeasonListener();
    }
  } catch (error) {
    console.error('Error loading dashboard stats:', error);
  }
}

// Calculate season stats from games data when team_season_stats is missing
async function calculateSeasonStatsFromGames(season) {
  try {
    // Get all games for the season
    const allGames = await getGames(season, null);
    console.log(`calculateSeasonStatsFromGames: Found ${allGames.length} games for season ${season}`);
    
    // Filter to regular season games with scores
    const regularSeasonGames = allGames.filter(game => {
      const correctedType = correctGameType(game);
      return correctedType === 'regular' && game.home_score !== null && game.away_score !== null;
    });
    
    console.log(`calculateSeasonStatsFromGames: Found ${regularSeasonGames.length} regular season games with scores`);
    
    // Calculate stats for each team
    const teamStats = {};
    
    // Initialize stats for all teams
    if (teamsData.length === 0) {
      const teams = await getTeams();
      teams.forEach(team => {
        teamStats[team.team_uid] = {
          stat_uid: `calculated_${season}_${team.team_uid}`,
          team_uid: team.team_uid,
          season: season,
          wins: 0,
          losses: 0,
          ties: 0,
          win_percentage: 0
        };
      });
    } else {
      teamsData.forEach(team => {
        teamStats[team.team_uid] = {
          stat_uid: `calculated_${season}_${team.team_uid}`,
          team_uid: team.team_uid,
          season: season,
          wins: 0,
          losses: 0,
          ties: 0,
          win_percentage: 0
        };
      });
    }
    
    // Process each game
    regularSeasonGames.forEach(game => {
      const homeWin = game.home_score > game.away_score;
      const tie = game.home_score === game.away_score;
      
      if (teamStats[game.home_team_uid]) {
        if (tie) {
          teamStats[game.home_team_uid].ties++;
        } else if (homeWin) {
          teamStats[game.home_team_uid].wins++;
        } else {
          teamStats[game.home_team_uid].losses++;
        }
      }
      
      if (teamStats[game.away_team_uid]) {
        if (tie) {
          teamStats[game.away_team_uid].ties++;
        } else if (!homeWin) {
          teamStats[game.away_team_uid].wins++;
        } else {
          teamStats[game.away_team_uid].losses++;
        }
      }
    });
    
    // Calculate win percentages and convert to array
    const calculatedStats = Object.values(teamStats).map(stat => {
      const totalGames = stat.wins + stat.losses + stat.ties;
      if (totalGames > 0) {
        stat.win_percentage = (stat.wins + (stat.ties * 0.5)) / totalGames;
      }
      return stat;
    });
    
    console.log(`calculateSeasonStatsFromGames: Calculated stats for ${calculatedStats.length} teams`);
    console.log('Sample calculated stat:', calculatedStats[0]);
    
    return calculatedStats;
  } catch (error) {
    console.error('Error calculating season stats from games:', error);
    return [];
  }
}

// Dedicated function to attach event listener
function attachDashboardSeasonListener() {
  const filterDropdown = document.getElementById('dashboard-season-filter');
  if (filterDropdown) {
    // Remove any existing listener to prevent duplicates
    filterDropdown.removeEventListener('change', loadDashboardStats);
    // Add the listener
    filterDropdown.addEventListener('change', (event) => {
      console.log('Dashboard season filter changed to:', event.target.value);
      loadDashboardStats();
    });
    console.log('Dashboard season filter listener attached to element with value:', filterDropdown.value);
  } else {
    console.error('Dashboard season filter dropdown not found');
  }
}

function renderDashboardStats(seasonStats, season) {
  console.log('renderDashboardStats: Rendering stats for season', season, 'with', seasonStats.length, 'teams');
  
  const statsSection = document.getElementById('dashboard-stats-section');
  
  // Calculate league-wide statistics
  const totalWins = seasonStats.reduce((sum, stat) => sum + (stat.wins || 0), 0);
  const totalLosses = seasonStats.reduce((sum, stat) => sum + (stat.losses || 0), 0);
  const avgWinPct = seasonStats.length > 0 ? seasonStats.reduce((sum, stat) => sum + (stat.win_percentage || 0), 0) / seasonStats.length : 0;
  
  // Find best and worst teams
  const bestTeam = seasonStats.length > 0 ? seasonStats.reduce((best, stat) => 
    (stat.win_percentage || 0) > (best.win_percentage || 0) ? stat : best
  ) : null;
  const worstTeam = seasonStats.length > 0 ? seasonStats.reduce((worst, stat) => 
    (stat.win_percentage || 0) < (worst.win_percentage || 0) ? stat : worst
  ) : null;
  
  statsSection.innerHTML = `
    <div class="flex justify-between items-center px-4 pb-3 pt-5">
      <h2 class="text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">${season} Season Insights</h2>
      <select id="dashboard-season-filter" class="rounded-lg bg-[#2e2348] text-white border border-[#423267] px-3 py-2">
        <option value="2024">2024 Season</option>
        <option value="2023">2023 Season</option>
        <option value="2022">2022 Season</option>
        <option value="2021">2021 Season</option>
      </select>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4">
      <div class="flex flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
        <p class="text-white text-base font-medium leading-normal">League Avg Win %</p>
        <p class="text-white tracking-light text-2xl font-bold leading-tight">${(avgWinPct * 100).toFixed(1)}%</p>
      </div>
      <div class="flex flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
        <p class="text-white text-base font-medium leading-normal">Total Regular Games</p>
        <p class="text-white tracking-light text-2xl font-bold leading-tight">${totalWins}</p> <!-- Total wins should equal total regular season games -->
      </div>
      <div class="flex flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
        <p class="text-white text-base font-medium leading-normal">Best Record</p>
        ${bestTeam ? `
          <p class="text-white tracking-light text-lg font-bold leading-tight">${getTeamName(bestTeam.team_uid)}</p>
          <p class="text-[#a292c9] text-sm">${bestTeam.wins}-${bestTeam.losses} (${(bestTeam.win_percentage * 100).toFixed(1)}%)</p>
        ` : `
          <p class="text-[#a292c9] text-sm">N/A</p>
        `}
      </div>
      <div class="flex flex-col gap-2 rounded-xl p-6 bg-[#2e2348]">
        <p class="text-white text-base font-medium leading-normal">Needs Improvement</p>
        ${worstTeam ? `
          <p class="text-white tracking-light text-lg font-bold leading-tight">${getTeamName(worstTeam.team_uid)}</p>
          <p class="text-[#a292c9] text-sm">${worstTeam.wins}-${worstTeam.losses} (${(worstTeam.win_percentage * 100).toFixed(1)}%)</p>
        ` : `
          <p class="text-[#a292c9] text-sm">N/A</p>
        `}
      </div>
    </div>

    <div class="p-4">
      <h3 class="text-white text-lg font-semibold mb-3">Top Performing Teams (${season})</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        ${seasonStats
          .sort((a, b) => (b.win_percentage || 0) - (a.win_percentage || 0))
          .slice(0, 6)
          .map(stat => {
            const team = teamsData.find(t => t.team_uid === stat.team_uid);
            return `
              <div class="flex items-center justify-between rounded-lg border border-[#423267] bg-[#2e2348] p-3">
                <div>
                  <p class="text-white text-sm font-medium">${team ? `${team.city} ${team.name}` : 'Unknown Team'}</p>
                  <p class="text-[#a292c9] text-xs">${team ? `${team.conference} ${team.division}` : ''}</p>
                </div>
                <div class="text-right">
                  <p class="text-white text-sm font-bold">${stat.wins}-${stat.losses}</p>
                  <p class="text-[#a292c9] text-xs">${(stat.win_percentage * 100).toFixed(1)}%</p>
                </div>
              </div>
            `;
          }).join('')}
      </div>
    </div>
  `;
  
  // Set the dropdown to the selected season and attach listener
  const filterDropdown = document.getElementById('dashboard-season-filter');
  if (filterDropdown) {
    filterDropdown.value = season;
    console.log('renderDashboardStats: Set dropdown value to', season);
  }
  
  // Use dedicated function to attach listener after DOM update
  setTimeout(() => {
    attachDashboardSeasonListener();
  }, 100); // Small delay to ensure DOM is fully updated
}

async function renderGameDetails(gameUid) {
  console.log('renderGameDetails called with gameUid:', gameUid);
  console.log('Available games in gamesData:', gamesData.length);
  console.log('Available games in filteredGamesData:', filteredGamesData.length);
  
  // Find the game in our loaded data
  const game = gamesData.find(g => g.game_uid === gameUid) || 
               filteredGamesData.find(g => g.game_uid === gameUid);
  
  console.log('Found game:', game);
  
  if (!game) {
    console.error('Game not found:', gameUid);
    console.error('Available game UIDs:', gamesData.slice(0, 5).map(g => g.game_uid));
    return;
  }

  const homeTeam = teamsData.find(t => t.team_uid === game.home_team_uid);
  const awayTeam = teamsData.find(t => t.team_uid === game.away_team_uid);

  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[1200px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <div class="flex items-center gap-3">
            <button id="back-to-games" class="flex cursor-pointer items-center justify-center rounded-lg h-8 px-3 bg-[#2e2348] text-white text-sm font-medium hover:bg-[#423267]">
              ← Back to Games
            </button>
          </div>
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">
            ${getTeamName(game.away_team_uid)} @ ${getTeamName(game.home_team_uid)}
          </p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">
            ${game.game_datetime ? new Date(game.game_datetime).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit'
            }) : 'Date TBD'} • ${getGameTypeDisplay(game.game_type)}${game.week ? ` Week ${Math.floor(game.week)}` : ''}
          </p>
        </div>
      </div>

      <div id="game-details-content" class="p-4">
        <div class="text-center text-[#a292c9]">Loading game details...</div>
      </div>
    </div>
  `;

  // Add back button listener
  document.getElementById('back-to-games').addEventListener('click', () => {
    switchPage('games');
  });

  // Load game statistics
  loadGameDetails(game, homeTeam, awayTeam);
}

async function loadGameDetails(game, homeTeam, awayTeam) {
  try {
    console.log('Loading game details for:', game.game_uid);

    // Load team game statistics for this specific game
    const gameStats = await getTeamGameStats(game.game_uid, null);
    console.log('Game stats loaded:', gameStats.length);

    // Load historical matchups between these teams
    const historicalMatchups = await getHistoricalMatchups(game.home_team_uid, game.away_team_uid);
    console.log('Historical matchups loaded:', historicalMatchups.length);

    // Separate home and away team stats
    const homeStats = gameStats.find(stat => stat.team_uid === game.home_team_uid);
    const awayStats = gameStats.find(stat => stat.team_uid === game.away_team_uid);

    renderGameDetailsContent(game, homeTeam, awayTeam, homeStats, awayStats, historicalMatchups);
  } catch (error) {
    console.error('Error loading game details:', error);
    const container = document.getElementById('game-details-content');
    container.innerHTML = `<p class="text-red-400 text-center">Error loading game details: ${error}</p>`;
  }
}

function renderGameDetailsContent(game, homeTeam, awayTeam, homeStats, awayStats, historicalMatchups = []) {
  const container = document.getElementById('game-details-content');
  
  const hasScore = game.home_score !== null && game.away_score !== null;
  const homeWin = hasScore && game.home_score > game.away_score;
  const awayWin = hasScore && game.away_score > game.home_score;
  const tie = hasScore && game.home_score === game.away_score;

  const weatherTemp = game.weather_temp ? 
    (temperatureUnit === 'celsius' ? `${Math.round((game.weather_temp - 32) * 5/9)}°C` : `${Math.round(game.weather_temp)}°F`) : '';

  container.innerHTML = `
    <!-- Game Summary -->
    <div class="mb-8">
      <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-6">
        <div class="grid grid-cols-3 gap-4 items-center">
          <!-- Away Team -->
          <div class="text-center">
            <h3 class="text-white text-xl font-bold mb-2">${awayTeam ? `${awayTeam.city} ${awayTeam.name}` : 'Unknown'}</h3>
            <p class="text-[#a292c9] text-sm mb-4">${awayTeam ? `${awayTeam.conference} ${awayTeam.division}` : ''}</p>
            <div class="text-center">
              <span class="text-white text-4xl font-bold ${awayWin ? 'text-green-400' : tie ? 'text-yellow-400' : ''}">${game.away_score ?? '-'}</span>
              ${awayWin ? '<p class="text-green-400 text-sm font-medium mt-1">WINNER</p>' : ''}
            </div>
          </div>

          <!-- VS and Game Info -->
          <div class="text-center">
            <p class="text-[#a292c9] text-lg font-medium mb-2">@</p>
            <div class="space-y-1">
              <p class="text-white text-sm">${game.venue || 'Venue TBD'}</p>
              <p class="text-[#a292c9] text-xs">${game.season} Season</p>
              ${game.attendance ? `<p class="text-[#a292c9] text-xs">Attendance: ${game.attendance.toLocaleString()}</p>` : ''}
              ${game.weather_condition ? `<p class="text-[#a292c9] text-xs">${game.weather_condition}${weatherTemp ? ` ${weatherTemp}` : ''}</p>` : ''}
              ${game.overtime ? '<p class="text-yellow-400 text-xs font-medium">OVERTIME</p>' : ''}
              ${tie ? '<p class="text-yellow-400 text-sm font-medium">TIE GAME</p>' : ''}
            </div>
          </div>

          <!-- Home Team -->
          <div class="text-center">
            <h3 class="text-white text-xl font-bold mb-2">${homeTeam ? `${homeTeam.city} ${homeTeam.name}` : 'Unknown'}</h3>
            <p class="text-[#a292c9] text-sm mb-4">${homeTeam ? `${homeTeam.conference} ${homeTeam.division}` : ''}</p>
            <div class="text-center">
              <span class="text-white text-4xl font-bold ${homeWin ? 'text-green-400' : tie ? 'text-yellow-400' : ''}">${game.home_score ?? '-'}</span>
              ${homeWin ? '<p class="text-green-400 text-sm font-medium mt-1">WINNER</p>' : ''}
            </div>
          </div>
        </div>
      </div>
    </div>

    ${(homeStats || awayStats) ? `
      <!-- Team Statistics Comparison -->
      <div class="mb-8">
        <h3 class="text-white text-xl font-bold mb-4">Team Performance</h3>
        <div class="rounded-xl border border-[#423267] bg-[#161122] overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="bg-[#211933]">
                <th class="px-4 py-3 text-left text-white text-sm font-medium">Statistic</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">${awayTeam ? awayTeam.abbreviation : 'Away'}</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">${homeTeam ? homeTeam.abbreviation : 'Home'}</th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-t border-[#423267]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">Total Yards</td>
                <td class="px-4 py-3 text-center text-white text-sm">${awayStats?.total_yards || '-'}</td>
                <td class="px-4 py-3 text-center text-white text-sm">${homeStats?.total_yards || '-'}</td>
              </tr>
              <tr class="border-t border-[#423267] hover:bg-[#2e2348]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">Passing Yards</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${awayStats?.passing_yards || '-'}</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${homeStats?.passing_yards || '-'}</td>
              </tr>
              <tr class="border-t border-[#423267]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">Rushing Yards</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${awayStats?.rushing_yards || '-'}</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${homeStats?.rushing_yards || '-'}</td>
              </tr>
              <tr class="border-t border-[#423267] hover:bg-[#2e2348]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">First Downs</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${awayStats?.first_downs || '-'}</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${homeStats?.first_downs || '-'}</td>
              </tr>
              <tr class="border-t border-[#423267]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">Turnovers</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${awayStats?.turnovers || '-'}</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${homeStats?.turnovers || '-'}</td>
              </tr>
              <tr class="border-t border-[#423267] hover:bg-[#2e2348]">
                <td class="px-4 py-3 text-[#a292c9] text-sm font-medium">Penalties</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${awayStats?.penalties || '-'}</td>
                <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${homeStats?.penalties || '-'}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Performance Analysis -->
      ${(homeStats && awayStats) ? `
        <div class="mb-8">
          <h3 class="text-white text-xl font-bold mb-4">Game Analysis</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Offensive Efficiency -->
            <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
              <h4 class="text-white text-lg font-semibold mb-3">Offensive Efficiency</h4>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-[#a292c9] text-sm">Yards per Play (${awayTeam?.abbreviation})</span>
                  <span class="text-white text-sm">${awayStats.total_yards && awayStats.total_yards > 0 ? (awayStats.total_yards / Math.max(1, (awayStats.first_downs || 1) * 3.3)).toFixed(1) : '-'}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#a292c9] text-sm">Yards per Play (${homeTeam?.abbreviation})</span>
                  <span class="text-white text-sm">${homeStats.total_yards && homeStats.total_yards > 0 ? (homeStats.total_yards / Math.max(1, (homeStats.first_downs || 1) * 3.3)).toFixed(1) : '-'}</span>
                </div>
              </div>
            </div>

            <!-- Turnover Battle -->
            <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
              <h4 class="text-white text-lg font-semibold mb-3">Turnover Battle</h4>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-[#a292c9] text-sm">Turnovers (${awayTeam?.abbreviation})</span>
                  <span class="text-white text-sm">${awayStats.turnovers || 0}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#a292c9] text-sm">Turnovers (${homeTeam?.abbreviation})</span>
                  <span class="text-white text-sm">${homeStats.turnovers || 0}</span>
                </div>
                <div class="flex justify-between border-t border-[#423267] pt-2">
                  <span class="text-[#a292c9] text-sm font-medium">Differential</span>
                  <span class="text-white text-sm font-medium">${(awayStats.turnovers || 0) - (homeStats.turnovers || 0) > 0 ? `+${(awayStats.turnovers || 0) - (homeStats.turnovers || 0)} ${homeTeam?.abbreviation}` : (homeStats.turnovers || 0) - (awayStats.turnovers || 0) > 0 ? `+${(homeStats.turnovers || 0) - (awayStats.turnovers || 0)} ${awayTeam?.abbreviation}` : 'Even'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ` : ''}
    ` : `
      <!-- No Statistics Available -->
      <div class="text-center text-[#a292c9] py-8">
        <p class="text-lg mb-2">No detailed statistics available for this game.</p>
        <p class="text-sm">Statistical data may not be available for all games in the database.</p>
      </div>
    `}

    <!-- Game Context & Environment -->
    <div class="mb-8">
      <h3 class="text-white text-xl font-bold mb-4">Game Context</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
          <p class="text-[#a292c9] text-sm mb-1">Season</p>
          <p class="text-white text-lg font-medium">${game.season}</p>
        </div>
        <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
          <p class="text-[#a292c9] text-sm mb-1">Week</p>
          <p class="text-white text-lg font-medium">${game.week ? Math.floor(game.week) : 'N/A'}</p>
        </div>
        <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
          <p class="text-[#a292c9] text-sm mb-1">Game Type</p>
          <p class="text-white text-lg font-medium">${getGameTypeDisplay(game.game_type)}</p>
        </div>
        ${game.attendance ? `
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
            <p class="text-[#a292c9] text-sm mb-1">Attendance</p>
            <p class="text-white text-lg font-medium">${game.attendance.toLocaleString()}</p>
          </div>
        ` : ''}
      </div>
      
      ${(game.weather_condition || game.weather_temp) ? `
        <div class="mt-4">
          <h4 class="text-white text-lg font-semibold mb-3">Weather Conditions</h4>
          <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4">
            <div class="flex justify-between items-center">
              <span class="text-[#a292c9] text-sm">Conditions</span>
              <span class="text-white text-sm font-medium">${game.weather_condition || 'N/A'}</span>
            </div>
            ${game.weather_temp ? `
              <div class="flex justify-between items-center mt-2">
                <span class="text-[#a292c9] text-sm">Temperature</span>
                <span class="text-white text-sm font-medium">${weatherTemp}</span>
              </div>
            ` : ''}
          </div>
        </div>
      ` : ''}
    </div>

    <!-- Historical Matchups -->
    ${historicalMatchups.length > 0 ? `
      <div class="mb-8">
        <h3 class="text-white text-xl font-bold mb-4">Historical Matchups</h3>
        <p class="text-[#a292c9] text-sm mb-4">Recent games between ${homeTeam?.abbreviation || 'Home'} and ${awayTeam?.abbreviation || 'Away'}</p>
        
        ${(() => {
          // Calculate head-to-head record
          let homeWins = 0, awayWins = 0, ties = 0;
          historicalMatchups.forEach(h => {
            if (h.home_score !== null && h.away_score !== null) {
              if (h.home_score > h.away_score) {
                if (h.home_team_uid === game.home_team_uid) homeWins++;
                else awayWins++;
              } else if (h.away_score > h.home_score) {
                if (h.away_team_uid === game.away_team_uid) awayWins++;
                else homeWins++;
              } else {
                ties++;
              }
            }
          });
          
          return `
            <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-4 mb-4">
              <h4 class="text-white text-lg font-semibold mb-2">All-Time Series Record</h4>
              <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p class="text-white text-xl font-bold">${homeWins}</p>
                  <p class="text-[#a292c9] text-sm">${homeTeam?.abbreviation || 'Home'}</p>
                </div>
                <div>
                  <p class="text-white text-xl font-bold">${ties}</p>
                  <p class="text-[#a292c9] text-sm">Ties</p>
                </div>
                <div>
                  <p class="text-white text-xl font-bold">${awayWins}</p>
                  <p class="text-[#a292c9] text-sm">${awayTeam?.abbreviation || 'Away'}</p>
                </div>
              </div>
            </div>
          `;
        })()}
        
        <div class="rounded-xl border border-[#423267] bg-[#161122] overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="bg-[#211933]">
                <th class="px-4 py-3 text-left text-white text-sm font-medium">Date</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Matchup</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Score</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Season</th>
                <th class="px-4 py-3 text-center text-white text-sm font-medium">Type</th>
              </tr>
            </thead>
            <tbody>
              ${historicalMatchups.slice(0, 10).map(h => {
                const hHasScore = h.home_score !== null && h.away_score !== null;
                const hHomeWin = hHasScore && h.home_score > h.away_score;
                const hAwayWin = hHasScore && h.away_score > h.home_score;
                const hTie = hHasScore && h.home_score === h.away_score;
                
                return `
                  <tr class="border-t border-[#423267] hover:bg-[#2e2348] cursor-pointer" onclick="handleGameRowClick('${h.game_uid}')">
                    <td class="px-4 py-3 text-[#a292c9] text-sm">
                      ${h.game_datetime ? new Date(h.game_datetime).toLocaleDateString() : 'TBD'}
                    </td>
                    <td class="px-4 py-3 text-center text-[#a292c9] text-sm">
                      ${getTeamName(h.away_team_uid)} @ ${getTeamName(h.home_team_uid)}
                    </td>
                    <td class="px-4 py-3 text-center text-sm">
                      ${hHasScore ? `
                        <span class="${hAwayWin ? 'text-green-400 font-medium' : hTie ? 'text-yellow-400' : 'text-[#a292c9]'}">${h.away_score}</span>
                        -
                        <span class="${hHomeWin ? 'text-green-400 font-medium' : hTie ? 'text-yellow-400' : 'text-[#a292c9]'}">${h.home_score}</span>
                        ${h.overtime ? ' (OT)' : ''}
                      ` : '<span class="text-[#a292c9]">Not played</span>'}
                    </td>
                    <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${h.season}</td>
                    <td class="px-4 py-3 text-center text-[#a292c9] text-sm">${getGameTypeDisplay(h.game_type)}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
        
        ${historicalMatchups.length > 10 ? `
          <p class="text-[#a292c9] text-sm text-center mt-2">
            Showing 10 of ${historicalMatchups.length} total matchups
          </p>
        ` : ''}
      </div>
    ` : ''}
  `;
}

function renderSettings() {
  const content = document.getElementById('app-content');
  content.innerHTML = `
    <div class="layout-content-container flex flex-col max-w-[960px] flex-1">
      <div class="flex flex-wrap justify-between gap-3 p-4">
        <div class="flex min-w-72 flex-col gap-3">
          <p class="text-white tracking-light text-[32px] font-bold leading-tight">Settings</p>
          <p class="text-[#a292c9] text-sm font-normal leading-normal">Configure your application preferences.</p>
        </div>
      </div>

      <div class="p-4">
        <div class="rounded-xl border border-[#423267] bg-[#2e2348] p-6">
          <h3 class="text-white text-lg font-semibold mb-4">Temperature Unit</h3>
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 text-white cursor-pointer">
              <input type="radio" name="temperature-unit" value="celsius" class="form-radio bg-[#161122] border-[#423267]" ${temperatureUnit === 'celsius' ? 'checked' : ''}>
              Celsius (°C)
            </label>
            <label class="flex items-center gap-2 text-white cursor-pointer">
              <input type="radio" name="temperature-unit" value="fahrenheit" class="form-radio bg-[#161122] border-[#423267]" ${temperatureUnit === 'fahrenheit' ? 'checked' : ''}>
              Fahrenheit (°F)
            </label>
          </div>
        </div>
      </div>
    </div>
  `;

  // Add event listener for temperature unit change
  document.querySelectorAll('input[name="temperature-unit"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      temperatureUnit = e.target.value;
      console.log('Temperature unit changed to:', temperatureUnit);
      // Re-render the current page if it's a game details page to reflect the change
      if (currentPage === 'game-detail') {
        const gameUid = document.querySelector('[data-game-uid]')?.dataset.gameUid;
        if (gameUid) {
          viewGameDetails(gameUid);
        }
      }
    });
  });
}

// Initialize app
window.addEventListener("DOMContentLoaded", async () => {
  console.log('App initializing...');
  
  // Load teams data immediately on app start
  try {
    console.log('Loading teams data on app startup...');
    teamsData = await getTeams();
    console.log('Teams loaded on startup:', teamsData.length);
  } catch (error) {
    console.error('Failed to load teams on startup:', error);
  }
  
  // Set up navigation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', async () => {
      await switchPage(link.dataset.page);
    });
  });
  
  // Load initial page
  switchPage('dashboard');
});
