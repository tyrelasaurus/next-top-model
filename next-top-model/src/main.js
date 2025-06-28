const { invoke } = window.__TAURI__.core;

let currentPage = 'dashboard';
let teamsData = [];
let gamesData = [];
let currentGamesPage = 1;
let gamesPerPage = 50;
let gamesSortBy = 'date';
let gamesSortDirection = 'desc';

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

function correctGameType(game) {
  if (!game.game_datetime) return game.game_type;
  
  const gameDate = new Date(game.game_datetime);
  const month = gameDate.getMonth() + 1; // JavaScript months are 0-indexed
  
  // Fix misclassified game types based on date
  if (month >= 8 && month <= 8) { // August
    return 'preseason';
  } else if (month >= 9 && month <= 12) { // September-December
    return 'regular';
  } else if (month >= 1 && month <= 2) { // January-February
    return 'playoff';
  }
  
  // Default to original type if date doesn't fit pattern
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
      </div>
    </div>
  `;
  
  // Load dashboard data
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    // Test database connection first
    const dbTest = await invoke("test_db_connection");
    console.log('Database test result:', dbTest);
    
    const games = await getGames();
    console.log('Dashboard loaded games:', games.length);
    document.getElementById('games-count').textContent = games.length;
    
    // Add event listeners for quick action buttons
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.getAttribute('data-page');
        console.log('Quick action clicked:', page);
        switchPage(page);
      });
    });
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
      <button class="team-games-btn flex cursor-pointer items-center justify-center overflow-hidden rounded-lg h-8 px-4 bg-[#423267] text-white text-sm font-medium leading-normal" data-team-uid="${team.team_uid}" data-team-name="${team.name}">
        View Games
      </button>
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

function renderGames() {
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
        <!-- Games will be loaded here -->
      </div>
    </div>
  `;
  
  loadGames();
  
  // Add event listeners
  document.getElementById('season-filter').addEventListener('change', filterGames);
  document.getElementById('game-type-filter').addEventListener('change', filterGames);
  document.getElementById('team-search').addEventListener('input', filterGames);
}

async function loadGames() {
  try {
    console.log('Loading games...');
    gamesData = await getGames();
    console.log('Games loaded:', gamesData.length);
    
    // Apply default sort (newest games first)
    gamesData = sortGames(gamesData, gamesSortBy, gamesSortDirection);
    filteredGamesData = gamesData; // Initialize filtered data
    currentGamesPage = 1; // Reset pagination
    renderGamesTable(gamesData);
  } catch (error) {
    console.error('Error loading games:', error);
    const container = document.getElementById('games-container');
    container.innerHTML = `<p class="text-red-400 text-center">Error loading games: ${error}</p>`;
  }
}

function renderGamesTable(games) {
  const container = document.getElementById('games-container');
  if (games.length === 0) {
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
          ${currentGames.map((game, index) => `
            <tr class="border-t border-t-[#423267] hover:bg-[#2e2348] cursor-pointer game-row" data-game-uid="${game.game_uid}">
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${game.game_datetime ? new Date(game.game_datetime).toLocaleDateString() : 'TBD'}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${getTeamName(game.away_team_uid)} @ ${getTeamName(game.home_team_uid)}
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
            </tr>
          `).join('')}
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
  
  // Add click handlers for game rows
  document.querySelectorAll('.game-row').forEach(row => {
    row.addEventListener('click', () => {
      const gameUid = row.getAttribute('data-game-uid');
      // For now, just show an alert - later this would navigate to game details
      alert(`Game details for ${gameUid} - Coming soon when we have more detailed game data!`);
    });
  });
  
  // Add sortable header event listeners
  document.querySelectorAll('.sortable-header').forEach(header => {
    header.addEventListener('click', () => {
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
  const team = teamsData.find(t => t.team_uid === teamUid);
  return team ? team.abbreviation || team.name : 'Unknown';
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
  console.log('Calculating standings with', games.length, 'games');
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
  
  // Calculate stats from games
  games.forEach(game => {
    // Check for regular season games (note: database uses 'regular', not 'Regular Season')
    if (game.home_score !== null && game.away_score !== null && game.game_type === 'regular') {
      regularSeasonGames++;
      const homeWin = game.home_score > game.away_score;
      
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
  
  console.log('Processed', regularSeasonGames, 'regular season games');
  
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
                      <td class="px-3 py-2 text-white text-sm">${stat.team.city} ${stat.team.name}</td>
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
}

// Navigation functions
function switchPage(page) {
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
      renderGames();
      break;
    case 'standings':
      renderStandings();
      break;
  }
}

function viewTeamGames(teamUid, teamName) {
  switchPage('games');
  // Wait for the games page to load, then filter by team abbreviation
  setTimeout(() => {
    const teamSearch = document.getElementById('team-search');
    if (teamSearch) {
      // Find the team to get its abbreviation
      const team = teamsData.find(t => t.team_uid === teamUid);
      const searchTerm = team ? (team.abbreviation || team.name) : teamName;
      teamSearch.value = searchTerm;
      filterGames();
    }
  }, 100);
}

// Initialize app
window.addEventListener("DOMContentLoaded", () => {
  // Set up navigation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      switchPage(link.dataset.page);
    });
  });
  
  // Load initial page
  switchPage('dashboard');
});
