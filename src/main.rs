
use std::{fmt::write, time::Duration};
use nba_eink_disp::*;

const TWOLVES_ID: &str = "1610612750";

#[tokio::main]
async fn main() {
    // let last = find_last_game(TWOLVES_ID).await;
    // println!("last: {:#?}", last);
    loop {
        let today = find_game_today(TWOLVES_ID).await;
        println!("today: {:#?}", today);
        if let Some(today) = today {
            let json = serde_json::to_string_pretty(&today).unwrap();
            std::fs::write("data/today.json", &json).unwrap();
            let box_score = get_game_boxscore(&today.id.to_string()).await;
            std::fs::write(format!("data/box-{}.json", chrono::Local::now()), &box_score).unwrap();
            let play = get_play_by_play(&today.id.to_string()).await;
            std::fs::write(&format!("data/play-{}.json", chrono::Local::now()), &play).unwrap();
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
    // let next = find_next_game(TWOLVES_ID).await;
    // println!("next: {:#?}", next);
}
