
use chrono::{DateTime, Datelike, Local, Utc};
use serde::{Serialize, Deserialize};

const TWOLVES_ID: &str = "1610612750";

#[tokio::main]
async fn main() {
    let last = find_last_game().await;
    println!("next: {:#?}", last);
    let next = find_next_game().await;
    println!("next: {:#?}", next);
}

async fn find_last_game() -> Game {
    let today = Local::now();
    for i in 0..5 {
        let url = url_for_date(today - chrono::Duration::days(i));
        let day: Day = reqwest::get(&url).await.unwrap().json().await.unwrap();
        for game in day.games.into_iter() {
            if game.home.id == TWOLVES_ID || game.away.id == TWOLVES_ID {
                if game.end_time.is_some() {
                    return game
                } 
            }
        }
    }
    panic!("Unable to find game in last 5 days");
}

async fn find_next_game() -> Game {
    let today = Local::now();
    for i in 0..5 {
        let url = url_for_date(today + chrono::Duration::days(i));
        let day: Day = reqwest::get(&url).await.unwrap().json().await.unwrap();
        for game in day.games.into_iter() {
            if game.home.id == TWOLVES_ID || game.away.id == TWOLVES_ID {
                if game.end_time.is_none() {
                    return game
                } 
            }
        }
    }
    panic!("Unable to find game in next 5 days");
}


#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Day {
    num_games: u8,
    games: Vec<Game>,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Game {
    #[serde(rename = "startTimeUTC")]
    start_time: chrono::DateTime<Utc>,
    #[serde(rename = "endTimeUTC")]
    end_time: Option<DateTime<Utc>>,
    clock: String,
    period: Period,
    #[serde(rename = "hTeam")]
    home: Team,
    #[serde(rename = "vTeam")]
    away: Team,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Period {
    current: u8,
    #[serde(rename = "type")]
    ty: u8,
    is_halftime: bool,
    is_end_of_period: bool,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Team {
    #[serde(rename = "teamId")]
    id: String,
    tri_code: String,
    win: String,
    loss: String,
    score: String,
    #[serde(rename = "linescore")]
    line_score: Vec<LineScore>,
}
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LineScore {
    score: String,
}

fn url_for_date(dt: impl Datelike) -> String {
    format!("https://data.nba.net/prod/v1/{}{:0>2}{:0>2}/scoreboard.json", dt.year(), dt.month(), dt.day())
}
