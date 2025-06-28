### **Analysis of Outstanding Issues & Recommended Fixes**

Here is a breakdown of the remaining critical bugs, their likely root causes, and a recommended plan to fix them.

---

#### **1. Dashboard: Season Insights Not Updating**

*   **Symptom:** The "Season Insights" section on the dashboard does not refresh when a new season is selected from the dropdown menu. It remains stuck on the initial 2024 data or stays empty.
*   **Root Cause Analysis:** The event listener responsible for triggering the data refresh is likely not being correctly attached or is being lost during DOM re-rendering. When `renderDashboardStats` is called and replaces the `innerHTML` of the stats section, the original `<select>` element with its listener is destroyed. The listener needs to be re-attached to the new element.
*   **Recommended Fix:**
    1.  **Consolidate Event Handling:** Modify the `renderDashboardStats` function. After setting the `innerHTML` for the stats section, immediately re-query the DOM for the `dashboard-season-filter` dropdown and attach the `addEventListener` to it right there. This ensures the listener is always present on the currently visible element.
    2.  **Verify Data Flow:** Add logging inside the `loadDashboardStats` function to confirm the correct `season` is being read from the dropdown and that the `getTeamSeasonStats` backend call is returning the expected data for that season.

---

#### **2. Team Details Page: Multiple Data-Related Bugs**

This page suffers from a fundamental data-loading and filtering problem. The issues are interconnected and stem from how data is fetched and passed between functions.

*   **Issue A: Season Records do not load.**
    *   **Symptom:** The "Season Records" section is always empty, showing "No season records available..." regardless of the team or season selected.
    *   **Root Cause Analysis:** The `loadTeamDetails` function is fetching season stats for the team, but the filtered result (`filteredSeasonStats`) is likely empty before it even gets to the rendering function. This could be because the initial fetch (`allTeamSeasonStats`) returns nothing or the subsequent filtering by season is failing.
    *   **Recommended Fix:** In `loadTeamDetails`, add a `console.log` immediately after the `const allTeamSeasonStats = await getTeamSeasonStats(null, teamUid);` line. Log the contents of `allTeamSeasonStats`. This will instantly reveal if the backend is providing the necessary data. If the data is present, the issue lies in the subsequent filtering logic.

*   **Issue B: Game Performance table shows all league games.**
    *   **Symptom:** The table of games on a team's detail page shows games for all teams, not just the one selected.
    *   **Root Cause Analysis:** This is a critical data filtering failure. The call to `getGames(null, teamUid)` is supposed to return games only for that `teamUid`. The fact that it's returning all games suggests either the backend `get_games` command is ignoring the `team_uid` parameter, or a global `gamesData` variable is being used by mistake instead of the filtered data.
    *   **Recommended Fix:** In `loadTeamDetails`, log the contents of `allTeamGames` right after the `await getGames(null, teamUid)` call. If that variable contains games from other teams, the backend query is the problem. If it's correct, then the wrong variable is being passed to the rendering function.

*   **Issue C: Season Averages are broken and missing stats.**
    *   **Symptom:** The averages section is missing several stats (Total Yards, Passing, etc.) and the remaining ones do not display any data.
    *   **Root Cause Analysis:** The data being passed to the `calculateTeamAverage` function (`gameStats`) lacks the necessary detailed statistical fields. The `getGames` function only returns basic game information (teams, score, date). The detailed stats (yards, turnovers) come from `getTeamGameStats`. The logic to combine these two data sources in the `enrichedGames` array is flawed or incomplete.
    *   **Recommended Fix:** The `loadTeamDetails` function must be refactored. It needs to fetch all games for the team, then loop through those games and fetch the detailed `game_stats` for each one. This detailed data must then be merged to create a complete `enrichedGames` array that includes all the fields required for the averages calculation.

---