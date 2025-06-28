# Next Top Model: Ratings. Rankings. Results.

A comprehensive NFL analytics application built with Tauri and Rust, providing in-depth team statistics, game analysis, and performance metrics for the 2021-2024 NFL seasons.

## Features

### 🏈 Comprehensive NFL Data
- **4 Seasons of Data**: Complete game records from 2021-2024 seasons
- **1,912 Games**: Every regular season and playoff game with detailed statistics
- **32 Teams**: Full league coverage with team profiles and performance metrics
- **Real-time Analysis**: Dynamic calculations of standings, averages, and performance indicators

### 📊 Advanced Analytics
- **Team Performance Metrics**: Yards per play, turnover differentials, offensive efficiency
- **Season Statistics**: Win/loss records, division standings, playoff appearances
- **Game-by-Game Analysis**: Detailed breakdowns of individual matchups
- **Historical Matchups**: Head-to-head records and trends between teams
- **Environmental Factors**: Weather conditions, game attendance, and stadium information

### 🎯 Key Features
- **Interactive Dashboard**: League-wide insights and top performers
- **Team Detail Pages**: Comprehensive team analytics with filtering by season
- **Game Details**: Click any game for complete statistics and analysis
- **Sortable Tables**: Sort by any column to find specific information quickly
- **Real-time Calculations**: Standings and statistics update dynamically

## Technology Stack

- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Backend**: Rust with Tauri framework
- **Database**: SQLite with comprehensive NFL data
- **Build Tool**: Tauri CLI for cross-platform desktop applications

## Installation

### Prerequisites
- [Node.js](https://nodejs.org/) (v16 or later)
- [Rust](https://www.rust-lang.org/) (latest stable)
- [Tauri Prerequisites](https://tauri.app/v1/guides/getting-started/prerequisites)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tyrelasaurus/next-top-model.git
cd next-top-model/next-top-model
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run tauri dev
```

4. Build for production:
```bash
npm run tauri build
```

## Project Structure

```
next-top-model/
├── src/                    # Frontend source files
│   ├── index.html         # Main HTML file
│   ├── main.js           # Application logic
│   └── styles.css        # Application styles
├── src-tauri/            # Rust backend
│   ├── src/
│   │   ├── lib.rs       # Main Rust logic and API commands
│   │   └── main.rs      # Application entry point
│   ├── Cargo.toml       # Rust dependencies
│   └── tauri.conf.json  # Tauri configuration
├── data/                 # SQLite database
│   └── nfl_data.db      # Comprehensive NFL statistics
└── package.json         # Node.js dependencies
```

## Database Schema

The application uses a SQLite database with the following key tables:

- **games**: All NFL games with scores, dates, and metadata
- **teams**: NFL team information including GPS coordinates
- **team_game_stats**: Detailed statistics for each team in each game
- **team_season_stats**: Aggregated season statistics for each team

## Usage

### Dashboard
The main dashboard provides:
- Current season standings
- League-wide statistics and averages
- Top performing teams
- Quick navigation to teams and games

### Team Pages
Click any team to view:
- Season-by-season records
- Game logs with opponent information
- Performance metrics and averages
- Home/away splits

### Game Details
Click any game to see:
- Complete box score
- Team statistics comparison
- Offensive efficiency metrics
- Turnover analysis
- Weather conditions and attendance

## Development

### API Commands

The Tauri backend exposes several commands:
- `get_teams()`: Fetch all NFL teams
- `get_games(season?)`: Fetch games, optionally filtered by season
- `get_team_details(team_id)`: Get comprehensive team information
- `get_game_details(game_id)`: Get detailed game statistics
- `get_team_season_stats(team_id, season)`: Get team's season statistics
- `get_team_game_stats(game_id)`: Get both teams' statistics for a game

### Debug Mode

Debug HTML files are available for testing:
- `debug.html`: Full data visualization testing
- `debug_simple.html`: Simplified debugging interface

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NFL data sourced from various public APIs and databases
- Built with [Tauri](https://tauri.app/) for cross-platform desktop support
- Stadium GPS coordinates for accurate team locations

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and updates.

---

**Current Version**: v2.0.0 - Advanced Analytics & Team Statistics

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
