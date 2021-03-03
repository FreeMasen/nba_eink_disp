use nba_eink_disp::*;
use std::{path::PathBuf, time::Duration};

use structopt::StructOpt;
#[derive(StructOpt)]
struct Args {
    /// The 3 letter team code to look for
    pub team: String,
    /// The output directory for the data files
    pub out_dir: PathBuf,
    /// The amount of time to wait between checking
    #[structopt(default_value = "1")]
    pub seconds: u64,
}

#[tokio::main]
async fn main() {
    let args = Args::from_args();
    pretty_env_logger::try_init().ok();
    let mut last_today = None;
    let mut last_play = None;
    if !args.out_dir.exists() {
        std::fs::create_dir_all(&args.out_dir).unwrap();
    }
    loop {
        let today = find_game_today(&args.team).await;
        if let Some(today) = today {
            log::debug!("Todays game: {:?}\n{:?} v {:?}", today.id, today.home.tri_code, today.away.tri_code);
            if let Some(play) = get_play_by_play(
                &today.id.to_string(),
                &today.home.tri_code,
                &today.away.tri_code,
            )
            .await
            {
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
                    std::fs::write(args.out_dir.join("today.json"), &json).unwrap();
                    *prev = today;
                }
            } else {
                let json = serde_json::to_string_pretty(&today).unwrap();
                std::fs::write(args.out_dir.join("today.json"), &json).unwrap();
                last_today = Some(today);
            }
        } else {
            std::fs::write(args.out_dir.join("today.json"), "{}").unwrap();
        }
        if let Some(last) = find_last_game(&args.team).await {
            if let Some(box_score) = get_game_boxscore(&last.id.to_string()).await {
                std::fs::write(args.out_dir.join("box_score.json"), &box_score).unwrap();
            } else {
                std::fs::write(args.out_dir.join("box_score.json"), "{}").unwrap();
            }
            let json = serde_json::to_string_pretty(&last).unwrap();
            std::fs::write(args.out_dir.join("last_game.json"), &json).unwrap();
        } else {
            std::fs::write(args.out_dir.join("last_game.json"), "{}").unwrap();
        }
        if let Some(next) = find_next_game(&args.team).await {
            let json = serde_json::to_string_pretty(&next).unwrap();
            std::fs::write(args.out_dir.join("next_game.json"), &json).unwrap();
        } else {
            std::fs::write(args.out_dir.join("next_game.json"), "{}").unwrap();
        }
        tokio::time::sleep(Duration::from_secs(args.seconds)).await;
    }
}
