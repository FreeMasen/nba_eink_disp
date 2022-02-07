use action::Action;
use chrono::{DateTime, Datelike, Local, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
pub mod action;
pub mod box_score;
pub mod render;

const TODAY_URL: &str =
    "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json";

pub enum Line {
    Small(String),
    Medium(String),
    Large(String),
}

impl Line {
    pub fn small(s: impl ToString) -> Self {
        Self::Small(s.to_string())
    }
    pub fn medium(s: impl ToString) -> Self {
        Self::Medium(s.to_string())
    }
    pub fn large(s: impl ToString) -> Self {
        Self::Large(s.to_string())
    }

    pub fn render(&self) -> String {
        match self {
            Line::Small(line) => format!("{}{}\n", 0, line),
            Line::Medium(line) => format!("{}{}\n", 1, line),
            Line::Large(line) => format!("{}{}\n", 2, line),
        }
    }
}

pub async fn find_last_game(team_avb: &str) -> Option<Game> {
    let today = Local::now();
    for i in 1..6 {
        let url = url_for_date(today - chrono::Duration::days(i));
        let s = request_with_retry(&url).await?;
        let day: Day = serde_json::from_str(&s)
            .map_err(|e| {
                log::error!("Failed to deserialize Day: {}", e);
                std::fs::write("day_err.json", &s).unwrap();
                e
            })
            .ok()?;
        for game in day.games.into_iter() {
            if game.home.tri_code == team_avb || game.away.tri_code == team_avb {
                if game.end_time.is_some() {
                    return Some(game);
                }
            }
        }
    }
    eprintln!("Failed to find game over the last 5 days");
    None
}

pub async fn find_game_today(team_abv: &str) -> Option<Game> {
    for _ in 0..5 {
        let json = request_with_retry(TODAY_URL).await?;
        let day: Today = serde_json::from_str(&json)
            .map_err(|e| {
                log::error!("failed to parse today, writing debug output: {}", e);
                std::fs::write("today_err.json", &json).unwrap();
                e
            })
            .ok()?;
        for mut game in day.scoreboard.games.into_iter() {
            if game.home.tri_code == team_abv || game.away.tri_code == team_abv {
                if let Some(new_clock) = action::duration_to_clock(&game.clock) {
                    game.clock = new_clock;
                } else {
                    log::warn!("Failed to parse clock: {:?}", game.clock);
                }
                return Some(game);
            }
        }
    }
    log::warn!("No game for teams {} in today", team_abv);
    None
}

pub async fn find_next_game(team_avb: &str) -> Option<Game> {
    let today = Local::now();
    for i in 1..6 {
        let url = url_for_date(today + chrono::Duration::days(i));
        let json = request_with_retry(&url).await?;
        std::fs::write("today.json", &json).unwrap();
        let day: Day = serde_json::from_str(&json)
            .map_err(|e| {
                log::error!("failed to deserailize next day");
                std::fs::write("next_day.json", &json).unwrap();
                e
            })
            .ok()?;
        for game in day.games.into_iter() {
            if game.home.tri_code == team_avb || game.away.tri_code == team_avb {
                if game.end_time.is_none() {
                    return Some(game);
                }
            }
        }
    }
    log::error!("Unable to find game in next 5 days");
    None
}

pub async fn get_game_boxscore(game_id: &str) -> Option<box_score::GameBoxScores> {
    let url = format!(
        "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{}.json",
        game_id
    );
    let s = request_with_retry(&url).await?;
    let bs: serde_json::Map<String, Value> = serde_json::from_str(&s)
        .map_err(|e| {
            log::error!("failed to parse box score json: {}", e);
            std::fs::write("box_score_err.json", s).unwrap();
            e
        })
        .ok()?;
    box_score::GameBoxScores::try_from_obj(&bs)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PlayByPlay {
    game: PlayByPlayGame,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PlayByPlayGame {
    pub actions: Vec<serde_json::Map<String, Value>>,
}

pub async fn get_play_by_play(
    game_id: &str,
    home_team: &str,
    away_team: &str,
) -> Option<Vec<Action>> {
    let url = format!(
        "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json",
        game_id
    );
    let content = request_with_retry(&url).await?;
    let play_by_play: serde_json::Map<String, Value> = serde_json::from_str(&content)
        .map_err(|e| {
            log::error!("failed to parse play by play json: {}", e);
            std::fs::write("play_by_play_err.json", &content).unwrap();
            e
        })
        .ok()?;
    let game = play_by_play.get("game").unwrap().as_object().unwrap();
    let actions = game.get("actions").unwrap().as_array().unwrap().to_owned();
    let mut ret: Vec<_> = actions
        .into_iter()
        .filter_map(|m| {
            action::Action::try_from_obj(m.as_object().unwrap().to_owned(), home_team, away_team)
        })
        .collect();
    ret.sort_by(|lhs, rhs| lhs.number().cmp(&rhs.number()));
    Some(ret)
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Day {
    num_games: u8,
    games: Vec<Game>,
}
#[derive(Debug, Serialize, Deserialize, PartialEq)]
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
    pub game_leaders: Option<GameLeaders>,
}

impl Game {
    pub fn has_ended(&self) -> bool {
        self.end_time.is_some() || self.clock == ""
    }

    pub fn is_active(&self) -> bool {
        dbg!(!self.has_ended()) && dbg!(self.start_time < Utc::now())
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(untagged)]
pub enum PeriodOrNumber {
    Period(Period),
    Number(u8),
}

impl PeriodOrNumber {
    pub fn as_number(&self) -> u8 {
        match self {
            Self::Period(inner) => inner.current,
            Self::Number(inner) => *inner,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Period {
    pub current: u8,
    #[serde(rename = "type")]
    pub ty: u8,
    pub is_halftime: bool,
    pub is_end_of_period: bool,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
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
    pub timeouts_remaining: Option<i8>,
    #[serde(alias = "linescore")]
    pub periods: Vec<LineScore>,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(untagged)]
pub enum StringOrNumber {
    String(String),
    Number(u32),
}

impl std::fmt::Display for StringOrNumber {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::String(s) => s.fmt(f),
            Self::Number(n) => n.fmt(f),
        }
    }
}

impl PartialEq<&str> for StringOrNumber {
    fn eq(&self, other: &&str) -> bool {
        match self {
            Self::String(s) => s == *other,
            Self::Number(n) => n.to_string() == *other,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct LineScore {
    score: StringOrNumber,
}

fn url_for_date(dt: impl Datelike) -> String {
    format!(
        "https://data.nba.net/prod/v1/{}{:0>2}{:0>2}/scoreboard.json",
        dt.year(),
        dt.month(),
        dt.day()
    )
}

async fn request_with_retry(url: &str) -> Option<String> {
    for i in 0..5 {
        match reqwest::get(url).await {
            Ok(res) => match res.text().await {
                Ok(text) => return Some(text),
                Err(e) => log::error!("({}) failed to get text from request to {}: {}", i, url, e),
            },
            Err(e) => log::error!("({}) failed to make request to {}: {}", i, url, e),
        }
        tokio::time::sleep(std::time::Duration::from_millis(i * 200)).await;
    }
    None
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Today {
    pub scoreboard: Scoreboard,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Scoreboard {
    pub game_date: String,
    pub league_id: String,
    pub games: Vec<Game>,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GameLeaders {
    pub home_leaders: GameLeader,
    pub away_leaders: GameLeader,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
enum Leaders {
    List(Vec<GameLeader>),
    Single(GameLeader),
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GameLeader {
    #[serde(alias = "personId")]
    pub id: StringOrNumber,
    #[serde(default)]
    pub name: String,
    #[serde(alias = "jerseyNum", default)]
    pub number: String,
    #[serde(default)]
    pub position: String,
    #[serde(default)]
    pub player_slug: Option<String>,
    #[serde(default)]
    pub points: u8,
    #[serde(default)]
    pub rebounds: u8,
    #[serde(default)]
    pub assists: u8,
}
