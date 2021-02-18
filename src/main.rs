
use nba_eink_disp::*;

const TWOLVES_ID: &str = "1610612750";

#[tokio::main]
async fn main() {
    let last = find_last_game(TWOLVES_ID).await;
    println!("last: {:#?}", last);
    let today = find_game_today(TWOLVES_ID).await;
    println!("today: {:#?}", today);
    if let Some(today) = today {
        let json = serde_json::to_string_pretty(&today).unwrap();
        std::fs::write("data/today.json", &json).unwrap();
    }
    let next = find_next_game(TWOLVES_ID).await;
    println!("next: {:#?}", next);
}
