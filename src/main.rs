use nba_eink_disp::*;
use std::time::Duration;

#[tokio::main]
async fn main() {
    let team_abv = std::env::args().skip(1).next().unwrap();
    let mut last_today = None;
    let mut last_box = None;
    let mut last_play = None;
    loop {
        let today = find_game_today(&team_abv).await;
        if let Some(today) = today {
            if let Some(box_score) = get_game_boxscore(&today.id.to_string()).await {
                if let Some(prev) = last_box.as_mut() {
                    if box_score != *prev {
                        let json = serde_json::to_string_pretty(&today).unwrap();
                        std::fs::write("data/box_score.json", &json).unwrap();
                        *prev = box_score;
                    }
                } else {
                    let json = serde_json::to_string_pretty(&today).unwrap();
                    std::fs::write("data/box_score.json", &json).unwrap();
                    last_box = Some(box_score);
                }
            }
            if let Some(play) = get_play_by_play(&today.id.to_string(), &today.home.tri_code, &today.away.tri_code).await {
                if let Some(prev) = last_play.as_mut() {
                    if play != *prev {
                        let json = serde_json::to_string_pretty(&play).unwrap();
                        std::fs::write("data/play_by_play.json", &json).unwrap();
                        *prev = play;
                    }
                } else {
                    let json = serde_json::to_string_pretty(&play).unwrap();
                    std::fs::write("data/play_by_play.json", &json).unwrap();
                    last_play = Some(play);
                }
            }
            if let Some(prev) = last_today.as_mut() {
                if today != *prev {
                    let json = serde_json::to_string_pretty(&today).unwrap();
                    std::fs::write("data/today.json", &json).unwrap();
                    *prev = today;
                }
            } else {
                let json = serde_json::to_string_pretty(&today).unwrap();
                std::fs::write("data/today.json", &json).unwrap();
                last_today = Some(today);
            }
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
}
