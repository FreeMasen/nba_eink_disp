use chrono::{DateTime, Datelike, Local, Utc};
use serde::{Serialize, Deserialize};

pub async fn find_last_game(team_id: &str) -> Game {
    let today = Local::now();
    for i in 0..5 {
        let url = url_for_date(today - chrono::Duration::days(i));
        let day: Day = reqwest::get(&url).await.unwrap().json().await.unwrap();
        for game in day.games.into_iter() {
            if game.home.id == team_id || game.away.id == team_id {
                if game.end_time.is_some() {
                    return game
                } 
            }
        }
    }
    panic!("Unable to find game in last 5 days");
}


pub async fn find_game_today(team_id: &str) -> Option<Game> {
    for _ in 0..5 {
        if let Ok(res) = reqwest::get("https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json").await {
            let json = res.text().await.unwrap();
            let day: Today = serde_json::from_str(&json).map_err(|e| {
                std::fs::write("today_err.json", &json).unwrap();                
                e
            }).unwrap();
            // let day = res.json::<Today>().await.unwrap();
            for game in day.scoreboard.games.into_iter() {
                if game.home.id == team_id || game.away.id == team_id {
                    return Some(game)
                }
            }
            return None
        }
    }
    None
}

pub async fn find_next_game(team_id: &str) -> Game {
    let today = Local::now();
    for i in 1..6 {
        let url = url_for_date(today + chrono::Duration::days(i));
        let day: Day = reqwest::get(&url).await.unwrap().json().await.unwrap();
        for game in day.games.into_iter() {
            if game.home.id == team_id || game.away.id == team_id {
                if game.end_time.is_none() {
                    return game
                } 
            }
        }
    }
    panic!("Unable to find game in next 5 days");
}

pub async fn get_game_boxscore(game_id: &str) -> String {
    let url = format!("https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{}.json", game_id);
    let s: serde_json::Value = reqwest::get(&url).await.unwrap().json().await.unwrap();
    serde_json::to_string_pretty(&s).unwrap()
}

pub async fn get_play_by_play(game_id: &str) -> String {
    let url = format!("https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json", game_id);
    let s: serde_json::Value = reqwest::get(&url).await.unwrap().json().await.unwrap();
    serde_json::to_string_pretty(&s).unwrap()
}


#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Day {
    num_games: u8,
    games: Vec<Game>,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Game {
    #[serde(alias = "gameId")]
    pub id: StringOrNumber,
    #[serde(alias = "startTimeUTC")]
    #[serde(alias = "gameTimeUTC")]
    pub start_time: chrono::DateTime<Utc>,
    #[serde(alias = "endTimeUTC")]
    end_time: Option<DateTime<Utc>>,
    #[serde(alias = "gameClock")]
    pub clock: String,
    pub period: PeriodOrNumber,
    #[serde(alias = "hTeam")]
    #[serde(alias = "homeTeam")]
    pub home: Team,
    #[serde(alias = "vTeam")]
    #[serde(alias = "awayTeam")]
    pub away: Team,
    pub game_leaders: Option<GameLeaders>
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum PeriodOrNumber {
    Period(Period),
    Number(u8),
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Period {
    pub current: u8,
    #[serde(rename = "type")]
    pub ty: u8,
    pub is_halftime: bool,
    pub is_end_of_period: bool,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Team {
    #[serde(alias = "teamId")]
    pub id: StringOrNumber,
    pub team_name: Option<String>,
    pub team_city: Option<String>,
    #[serde(alias = "teamTricode")]
    pub tri_code: String,
    #[serde(alias = "wins")]
    pub win: StringOrNumber,
    #[serde(alias = "losses")]
    pub loss: StringOrNumber,
    pub score: StringOrNumber,
    pub in_bonus: Option<StringOrNumber>,
    pub timeouts_remaining: Option<u8>,
    #[serde(alias = "linescore")]
    pub periods: Vec<LineScore>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum StringOrNumber {
    String(String),
    Number(u32)
}

impl PartialEq<&str> for StringOrNumber {
    fn eq(&self, other: &&str) -> bool {
        match self {
            Self::String(s) => s == *other,
            Self::Number(n) => n.to_string() == *other
        }
    }
}

impl ToString for StringOrNumber {
    fn to_string(&self) -> String {
        match self {
            Self::Number(n) => n.to_string(),
            Self::String(s) => s.to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LineScore {
    score: StringOrNumber,
}

fn url_for_date(dt: impl Datelike) -> String {
    format!("https://data.nba.net/prod/v1/{}{:0>2}{:0>2}/scoreboard.json", dt.year(), dt.month(), dt.day())
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Today {
    pub scoreboard: Scoreboard
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Scoreboard {
    pub game_date: String,
    pub league_id: String,
    pub games: Vec<Game>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GameLeaders {
    pub home_leaders: GameLeader,
    pub away_leaders: GameLeader,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
enum Leaders {
    List(Vec<GameLeader>),
    Single(GameLeader)
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GameLeader {
    #[serde(alias = "personId")]
    pub id: StringOrNumber,
    #[serde(default)]
    pub name: String,
    #[serde(alias = "jerseyNum")]
    pub number: String,
    pub position: String,
    pub player_slug: Option<String>,
    pub points: u8,
    pub rebounds: u8,
    pub assists: u8,
}

// {
//     "actionNumber": 2,
//     "actionType": "period",
//     "clock": "PT12M00.00S",
//     "description": "Period Start",
//     "edited": "2021-02-18T01:10:24Z",
//     "isFieldGoal": 0,
//     "orderNumber": 20000,
//     "period": 1,
//     "periodType": "REGULAR",
//     "personId": 0,
//     "personIdsFilter": [],
//     "possession": 0,
//     "qualifiers": [],
//     "scoreAway": "0",
//     "scoreHome": "0",
//     "side": null,
//     "subType": "start",
//     "timeActual": "2021-02-18T01:10:24.1Z",
//     "x": null,
//     "xLegacy": null,
//     "y": null,
//     "yLegacy": null
//   },
