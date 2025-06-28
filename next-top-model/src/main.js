const { invoke } = window.__TAURI__.core;

let currentPage = 'dashboard';
let teamsData = [];
let gamesData = [];
let currentGamesPage = 1;
let gamesPerPage = 50;

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
    return await invoke("get_games", { season, team_uid: teamUid });
  } catch (error) {
    console.error("Error fetching games:", error);
    return [];
  }
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
          <option value="Regular Season">Regular Season</option>
          <option value="Playoffs">Playoffs</option>
          <option value="Preseason">Preseason</option>
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
  
  container.innerHTML = `
    <div class="flex overflow-hidden rounded-xl border border-[#423267] bg-[#161122]">
      <table class="flex-1">
        <thead>
          <tr class="bg-[#211933]">
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Date</th>
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Matchup</th>
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Score</th>
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Type</th>
            <th class="px-4 py-3 text-left text-white text-sm font-medium leading-normal">Season</th>
          </tr>
        </thead>
        <tbody>
          ${games.slice(0, 50).map(game => `
            <tr class="border-t border-t-[#423267]">
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
                ${game.game_type || 'N/A'}${game.week ? ` (Week ${Math.floor(game.week)})` : ''}
              </td>
              <td class="px-4 py-2 text-[#a292c9] text-sm font-normal leading-normal">
                ${game.season}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    ${games.length > 50 ? `<p class="text-[#a292c9] text-center mt-4">Showing first 50 of ${games.length} games</p>` : ''}
  `;
}

function getTeamName(teamUid) {
  const team = teamsData.find(t => t.team_uid === teamUid);
  return team ? team.abbreviation || team.name : 'Unknown';
}

function filterGames() {
  const seasonFilter = document.getElementById('season-filter').value;
  const gameTypeFilter = document.getElementById('game-type-filter').value;
  const teamSearch = document.getElementById('team-search').value.toLowerCase();
  
  const filteredGames = gamesData.filter(game => {
    const seasonMatch = seasonFilter === '' || game.season.toString() === seasonFilter;
    const typeMatch = gameTypeFilter === '' || game.game_type === gameTypeFilter;
    const teamMatch = teamSearch === '' || 
      getTeamName(game.home_team_uid).toLowerCase().includes(teamSearch) ||
      getTeamName(game.away_team_uid).toLowerCase().includes(teamSearch);
    
    return seasonMatch && typeMatch && teamMatch;
  });
  
  renderGamesTable(filteredGames);
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
  
  // Calculate stats from games
  games.forEach(game => {
    if (game.home_score !== null && game.away_score !== null && game.game_type === 'Regular Season') {
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
  // Wait for the games page to load, then filter by team
  setTimeout(() => {
    const teamSearch = document.getElementById('team-search');
    if (teamSearch) {
      teamSearch.value = teamName;
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
