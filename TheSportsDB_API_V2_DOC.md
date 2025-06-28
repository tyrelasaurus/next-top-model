# TheSportsDB API V2 Reference

## Authentication

- All requests must include your API key in the header:  
  `X-API-KEY: <your-api-key>`

## Rate Limits

| User Tier | Requests per Minute |
|-----------|--------------------|
| Free      | 30                 |
| Premium   | 100                |
| Business  | 120                |

- If you exceed your rate limit, you'll receive HTTP 429 and must wait one minute before retrying.

## API Endpoints

### Search

- **League:**  
  `/api/v2/json/search/league/{league_name}`  
  Example: `/api/v2/json/search/league/english_premier_league`

- **Team:**  
  `/api/v2/json/search/team/{team_name}`  
  Example: `/api/v2/json/search/team/manchester_united`

- **Player:**  
  `/api/v2/json/search/player/{player_name}`  
  Example: `/api/v2/json/search/player/harry_kane`

- **Event:**  
  `/api/v2/json/search/event/{event_name}`  
  Example: `/api/v2/json/search/event/fifa_world_cup_2022-12-18_argentina_vs_france`

- **Venue:**  
  `/api/v2/json/search/venue/{venue_name}`  
  Example: `/api/v2/json/search/venue/wembley`

---

### Lookup

- **League:** `/api/v2/json/lookup/league/{idLeague}`
- **Team:** `/api/v2/json/lookup/team/{idTeam}`
- **Team Equipment:** `/api/v2/json/lookup/team_equipment/{idTeam}`
- **Player:** `/api/v2/json/lookup/player/{idPlayer}`
- **Player Contracts:** `/api/v2/json/lookup/player_contracts/{idPlayer}`
- **Player Honours:** `/api/v2/json/lookup/player_honours/{idPlayer}`
- **Player Milestones:** `/api/v2/json/lookup/player_milestones/{idPlayer}`
- **Player Former Teams:** `/api/v2/json/lookup/player_teams/{idPlayer}`
- **Event:** `/api/v2/json/lookup/event/{idEvent}`
- **Event Lineup:** `/api/v2/json/lookup/event_lineup/{idEvent}`
- **Event Results:** `/api/v2/json/lookup/event_results/{idEvent}`
- **Event Statistics:** `/api/v2/json/lookup/event_stats/{idEvent}`
- **Event Timeline:** `/api/v2/json/lookup/event_timeline/{idEvent}`
- **Event TV Schedule:** `/api/v2/json/lookup/event_tv/{idEvent}`
- **Event Youtube Highlights:** `/api/v2/json/lookup/event_highlights/{idEvent}`
- **Venue:** `/api/v2/json/lookup/venue/{idVenue}`

---

### List

- **League Teams:** `/api/v2/json/list/teams/{idLeague}`
- **League Seasons:** `/api/v2/json/list/seasons/{idLeague}`
- **League Season Posters:** `/api/v2/json/list/seasonposters/{idLeague}`
- **Team Players:** `/api/v2/json/list/players/{idTeam}`

---

### Filter (TV Events)

- **By Date:** `/api/v2/json/filter/tv/day/{dateEvent}`
- **By Country:** `/api/v2/json/filter/tv/country/{strCountry}`
- **By Sport:** `/api/v2/json/filter/tv/sport/{strSport}`
- **By Channel:** `/api/v2/json/filter/tv/channel/{strChannel}`

---

### All

- **Countries:** `/api/v2/json/all/countries`
- **Sports:** `/api/v2/json/all/sports`
- **Leagues:** `/api/v2/json/all/leagues`

---

### Schedule

- **Next 10 Events in League:** `/api/v2/json/schedule/next/league/{idLeague}`
- **Previous 10 Events in League:** `/api/v2/json/schedule/previous/league/{idLeague}`
- **Next 10 Events in Team:** `/api/v2/json/schedule/next/team/{idTeam}`
- **Previous 10 Events in Team:** `/api/v2/json/schedule/previous/team/{idTeam}`
- **Next 10 Events in Venue:** `/api/v2/json/schedule/next/venue/{idVenue}`
- **Previous 10 Events in Venue:** `/api/v2/json/schedule/previous/venue/{idVenue}`
- **Full Team Season Schedule:** `/api/v2/json/schedule/full/team/{idTeam}`
- **Full League Season Schedule:** `/api/v2/json/schedule/league/{idLeague}/{season}`

---

### Livescores

- **Sport:** `/api/v2/json/livescore/{strSport}`
- **League:** `/api/v2/json/livescore/{idLeague}`
- **All:** `/api/v2/json/livescore/all`

---

## Example: Livescore JSON Fields

- `idLiveScore`: ~9-digit dynamic API id (not useful)
- `idEvent`: ~7-digit event id
- `strSport`: e.g. "American Football"
- `idLeague`: e.g. "4391"
- `strLeague`: e.g. "NFL"
- `idHomeTeam`, `idAwayTeam`: 6-digit team IDs
- `strHomeTeam`, `strAwayTeam`: Full team names
- `strHomeTeamBadge`, `strAwayTeamBadge`: Team logo URLs
- `intHomeScore`, `intAwayScore`: Numeric scores
- `strProgress`: e.g. "mm:ss - Xst/nd/rd/th" or "Final"
- `strEventTime`: Start time of the game
- `dateEvent`: Date of the game (API feed's local TZ)
- `updated`: Date and time stamp of the API feed

---

## Event Status Codes

<details>
<summary>American Football</summary>

| Code | Meaning                |
|------|------------------------|
| NS   | Not Started            |
| Q1   | First Quarter (In Play)|
| Q2   | Second Quarter         |
| Q3   | Third Quarter          |
| Q4   | Fourth Quarter         |
| OT   | Overtime               |
| HT   | Halftime               |
| FT   | Finished               |
| AOT  | After Over Time        |
| CANC | Cancelled              |
| PST  | Postponed              |
</details>

<details>
<summary>Baseball</summary>

| Code | Meaning                |
|------|------------------------|
| NS   | Not Started            |
| IN1  | Inning 1 (In Play)     |
| IN2  | Inning 2 (In Play)     |
| IN3  | Inning 3 (In Play)     |
| IN4  | Inning 4 (In Play)     |
| IN5  | Inning 5 (In Play)     |
| IN6  | Inning 6 (In Play)     |
| IN7  | Inning 7 (In Play)     |
| IN8  | Inning 8 (In Play)     |
| IN9  | Inning 9 (In Play)     |
| POST | Postponed              |
| CANC | Cancelled              |
| INTR | Interrupted            |
| ABD  | Abandoned              |
| FT   | Finished               |
</details>

<details>
<summary>Basketball</summary>

| Code | Meaning                |
|------|------------------------|
| NS   | Not Started            |
| Q1   | Quarter 1 (In Play)    |
| Q2   | Quarter 2 (In Play)    |
| Q3   | Quarter 3 (In Play)    |
| Q4   | Quarter 4 (In Play)    |
| OT   | Over Time (In Play)    |
| BT   | Break Time (In Play)   |
| HT   | Halftime (In Play)    |
| FT   | Game Finished          |
| AOT  | After Over Time        |
| POST | Game Postponed        |
| CANC | Game Cancelled        |
| SUSP | Game Suspended        |
| AWD  | Game Awarded          |
| ABD  | Game Abandoned        |
</details>

<details>
<summary>Soccer</summary>

| Code | Meaning                |
|------|------------------------|
| TBD  | Time To Be Defined     |
| NS   | Not Started            |
| 1H   | First Half, Kick Off   |
| HT   | Halftime               |
| 2H   | Second Half, 2nd Half Started|
| ET   | Extra Time             |
| P    | Penalty In Progress    |
| FT   | Match Finished         |
| AET  | Match Finished After Extra Time|
| PEN  | Match Finished After Penalty|
| BT   | Break Time (in Extra Time)|
| SUSP | Match Suspended        |
| INT  | Match Interrupted      |
| PST  | Match Postponed       |
| CANC | Match Cancelled        |
| ABD  | Match Abandoned        |
| AWD  | Technical Loss         |
| WO   | WalkOver               |
</details>

<details>
<summary>Other Sports</summary>

- Handball, Ice Hockey, Rugby, Volleyball: See original documentation for full code lists.
</details>

---

## Rounds (Special Codes)

| Code | Meaning                |
|------|------------------------|
| 125  | Quarter-Final          |
| 150  | Semi-Final             |
| 160  | Playoff                |
| 170  | Playoff Semi-Final     |
| 180  | Playoff Final          |
| 200  | Final                  |
| 400  | Qualifier              |
| 500  | Pre-Season             |

---

## OpenAPI Specification

- [OpenAPI YAML](https://www.thesportsdb.com/api/spec/v2/openapi.yaml)

---
Type:  Limit: 
Example: Static / Live
List the next 5 events for a team using its unique ID {idTeam}
/api/v2/json/schedule/next/team/133612

Previous 10 Events in Team
Type:  Limit: 
Example: Static / Live
List the previous 5 events for a team using its unique ID {idTeam}
/api/v2/json/schedule/previous/team/133612

Next 10 Events in Venue
Type:  Limit: 
Example: Static / Live
List the next 5 events for a venue using its unique ID {idVenue}
/api/v2/json/schedule/next/venue/24413

Previous 10 Events in Venue
Type:  Limit: 
Example: Static / Live
List the previous 5 events for a venue using its unique ID {idVenue}
/api/v2/json/schedule/previous/venue/24413

Full Team Season Schedule
Type:  Limit: 
Example: Static / Live
List the full seasons schedule for a team using its unique ID {idTeam}
/api/v2/json/schedule/full/team/133612

Full League Season Schedule
Type:  Limit: 
Example: Static / Live
List the full seasons schedule for a league using its unique ID {idLeague}
/api/v2/json/schedule/league/4328/2023-2024


seperator bar


 v2 API Livescores
Livescore Sport
Type:  Limit: 
Example: Static / Live
Show the current Livescores for a particular sport {strSport}
/api/v2/json/livescore/soccer

Livescore League
Type:  Limit: 
Example: Static / Live
Show the current Livescores for a particular league by its unique ID {idLeague}
/api/v2/json/livescore/4399

Livescore All
Type:  Limit: 
Example: Static / Live
Show the current Livescores for all sports.
/api/v2/json/livescore/all

OpenAPI information: https://www.thesportsdb.com/api/spec/v2/openapi.yaml

API Data
Livescore
Example JSON
[idLiveScore] => // ~9-digit dynamic api id (not useful)
[idEvent] => // ~7-digit event id
[strSport] => // "American Football"
[idLeague] => // "4391"
[strLeague] => // "NFL"
[idHomeTeam] => // 6-digit fixed NFL Team No.
[idAwayTeam] => // 6-digit fixed NFL Team No.
[strHomeTeam] => // Full name of the NFL Team
[strAwayTeam] => // Full name of the NFL Team
[strHomeTeamBadge] => // .PNG image file of the NFL Team's logo
[strAwayTeamBadge] => // .PNG image file of the NFL Team's logo
[intHomeScore] => // Home Team's numeric game's progress score
[intAwayScore] => // Away Team's numeric game's progress score
[intEventScore] => // (empty/unused)
[intEventScoreTotal] => // (empty/unused)
[strStatus] => // (empty/unused)
[strProgress] => // "mm:ss - Xst/nd/rd/th" OR "Final" (not yet sure of pre-game or overtime yet as I am still building & testing)
[strEventTime] => // start time of the game -- appears to be dynamic/changes (?)
[dateEvent] => // date of the game according to the API feed's local TZ
[updated] => // date and time stamp of the API feed

Event Status
American Football
NS : Not Started
Q1 : First Quarter (In Play)
Q2 : Second Quarter (In Play)
Q3 : Third Quarter (In Play)
Q4 : Fourth Quarter (In Play)
OT : Overtime (In Play)
HT : Halftime (In Play)
FT : Finished (Game Finished)
AOT : After Over Time (Game Finished)
CANC : Cancelled (Game cancelled and not rescheduled)
PST : Postponed (Game postponed and waiting for a new game date)

Baseball
NS : Not Started
IN1 : Inning 1 (In Play)
IN2 : Inning 2 (In Play)
IN3 : Inning 3 (In Play)
IN4 : Inning 4 (In Play)
IN5 : Inning 5 (In Play)
IN6 : Inning 6 (In Play)
IN7 : Inning 7 (In Play)
IN8 : Inning 8 (In Play)
IN9 : Inning 9 (In Play)
POST : Postponed
CANC : Cancelled
INTR : Interrupted
ABD : Abandoned
FT : Finished (Game Finished)

Basketball
NS : Not Started
Q1 : Quarter 1 (In Play)
Q2 : Quarter 2 (In Play)
Q3 : Quarter 3 (In Play)
Q4 : Quarter 4 (In Play)
OT : Over Time (In Play)
BT : Break Time (In Play)
HT : Halftime (In Play)
FT : Game Finished (Game Finished)
AOT : After Over Time (Game Finished)
POST : Game Postponed
CANC : Game Cancelled
SUSP : Game Suspended
AWD : Game Awarded
ABD : Game Abandoned

Soccer
TBD : Time To Be Defined
NS : Not Started
1H : First Half, Kick Off
HT : Halftime
2H : Second Half, 2nd Half Started
ET : Extra Time
P : Penalty In Progress
FT : Match Finished
AET : Match Finished After Extra Time
PEN : Match Finished After Penalty
BT : Break Time (in Extra Time)
SUSP : Match Suspended
INT : Match Interrupted
PST : Match Postponed
CANC : Match Cancelled
ABD : Match Abandoned
AWD : Technical Loss
WO : WalkOver

Handball
NS : Not Started
1H : First Half (In Play)
2H : Second Half (In Play)
HT : Half Time (In Play)
ET : Extra Time (In Play)
BT : Break Time (In Play)
PT : Penalties Time (In Play)
AW : Awarded
POST : Postponed
CANC : Cancelled
INTR : Interrupted
ABD : Abandoned
WO : Walkover
AET : After Extra Time (Game Finished)
AP : After Penalties (Game Finished)
FT : Finished (Game Finished)

Ice Hockey
NS : Not Started
P1 : First Period (In Play)
P2 : Second Period (In Play)
P3 : Third Period (In Play)
OT : Over Time (In Play)
PT : Penalties Time (In Play)
BT : Break Time (In Play)
AW : Awarded
POST : Postponed
CANC : Cancelled
INTR : Interrupted
ABD : Abandoned
AOT : After Over Time (Game Finished)
AP : After Penalties (Game Finished)
FT : Finished (Game Finished)

Rugby
NS : Not Started
1H : First Half (In Play)
2H : Second Half (In Play)
HT : Half Time (In Play)
ET : Extra Time (In Play)
BT : Break Time (In Play)
PT : Penalties Time (In Play)
AW : Awarded
POST : Postponed
CANC : Cancelled
INTR : Interrupted
ABD : Abandoned
AET : After Extra Time (Game Finished)
FT : Finished (Game Finished)

Volleyball
NS : Not Started
S1 : Set 1 (In Play)
S2 : Set 2 (In Play)
S3 : Set 3 (In Play)
S4 : Set 4 (In Play)
S5 : Set 5 (In Play)
AW : Awarded
POST : Postponed
CANC : Cancelled
INTR : Interrupted
ABD : Abandoned
FT : Finished (Game Finished)

Rounds
Special
125 = Quarter-Final
150 = Semi-Final
160 = Playoff
170 = Playoff Semi-Final
180 = Playoff Final
200 = Final
400 = Qualifier
500 = Pre-Season
