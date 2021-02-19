use nba_eink_disp::*;
use std::{fmt::write, time::Duration};

const TWOLVES_ID: &str = "1610612750";

#[tokio::main]
async fn main() {
    // let last = find_last_game(TWOLVES_ID).await;
    // println!("last: {:#?}", last);
    let team_abv = std::env::args().skip(1).next().unwrap();
    loop {
        let today = find_game_today(&team_abv).await;
        if let Some(today) = today {
            let json = serde_json::to_string_pretty(&today).unwrap();
            std::fs::write("data/today.json", &json).unwrap();
            let box_score = get_game_boxscore(&today.id.to_string()).await;
            std::fs::write("data/box_score.json",
                &box_score,
            )
            .unwrap();
            if let Some(play) = get_play_by_play(&today.id.to_string(), &today.home.tri_code, &today.away.tri_code).await {
                let json = serde_json::to_string_pretty(&play).unwrap();
                std::fs::write("data/play_by_play.json", &json).unwrap();
            }
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
    // let next = find_next_game(TWOLVES_ID).await;
    // println!("next: {:#?}", next);
}
