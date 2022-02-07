use nba_eink_disp::*;
use std::{
    path::{Path, PathBuf},
    time::Duration,
};

use structopt::StructOpt;
#[derive(StructOpt)]
struct Args {
    /// The 3 letter team code to look for
    pub team: String,
    /// The output directory for the data files
    pub out_dir: PathBuf,
    /// The amount of time to wait between checking
    #[structopt(default_value = "5")]
    pub seconds: u64,
}

#[tokio::main]
async fn main() {
    let args = Args::from_args();
    pretty_env_logger::try_init().ok();
    if !args.out_dir.exists() {
        std::fs::create_dir_all(&args.out_dir).unwrap();
    }
    loop {
        tick(&args.team, args.out_dir.join("datafile"), args.seconds).await;
        tokio::time::sleep(Duration::from_secs(args.seconds)).await;
    }
}

async fn tick(team: &str, file: impl AsRef<Path>, tick: u64) {
    if let Some(today) = find_game_today(team).await {
        let mut game = render::game(&today);
        if today.has_ended() {
            game_ended(today, team, file.as_ref(), tick).await;
            return;
        }
        if today.is_active() {
            let plays = get_play_by_play(
                &today.id.to_string(),
                &today.home.tri_code,
                &today.away.tri_code,
            )
            .await
            .unwrap_or_else(Vec::new);
            if let Some(last_play) = plays.last() {
                game += &render::action(&last_play)
            }
        }

        std::fs::write(file, &game).unwrap();
        log::debug!("updating today's game info");
        return;
    }
    if let Some(last) = find_last_game(team).await {
        log::debug!("updating last game info");
        game_ended(last, team, file.as_ref(), tick).await;
        return;
    }
    if let Some(next) = find_next_game(team).await {
        log::debug!("updating next game info");
        std::fs::write(file, &render::game(&next)).unwrap();
        return;
    }
    std::fs::write(file, Line::large("No Game Found").render()).unwrap();
    log::warn!("no next game found");
}

async fn game_ended(game: Game, team: &str, file: impl AsRef<Path>, tick: u64) {
    let base = render::game(&game);
    let next_game = find_next_game(team).await;
    let next = next_game
        .as_ref()
        .map(|g| g.start_time)
        .unwrap_or_else(|| chrono::Utc::now() + chrono::Duration::hours(12));
    let trailer = if let Some(next) = next_game.as_ref() {
        render::game(next)
    } else {
        String::new()
    };
    let mut box_score = get_game_boxscore(&game.id.to_string()).await.map(|b| {
        log::debug!("found box scores");
        if b.home.abv.eq_ignore_ascii_case(team) {
            b.home.box_score
        } else {
            b.away.box_score
        }
    });
    let mut box_score_idxs = box_score.as_ref().map(get_indexes).map(|idxs| idxs.into_iter().cycle());
    while chrono::Utc::now() < next {
        let mut buffer = base.clone();
        if let Some(box_score) = box_score.as_ref() {
            if let Some(iter) = box_score_idxs.as_mut() {
                if let Some(idx) = iter.next() {
                    if let Some(box_info) = render::box_score(box_score, idx) {
                        buffer += &box_info;
                    }
                }
            }
        } else if let Some(b) = get_game_boxscore(&game.id.to_string()).await {
            box_score = if b.home.abv.eq_ignore_ascii_case(team) {
                Some(b.home.box_score)
            } else {
                Some(b.away.box_score)
            };
            box_score_idxs = box_score.as_ref().map(get_indexes).map(|idxs| idxs.into_iter().cycle());
        }
        std::fs::write(file.as_ref(), format!("{}{}", buffer, trailer)).unwrap();
        tokio::time::sleep(Duration::from_secs(tick)).await;
    }

}

fn get_indexes(box_scores: &nba_eink_disp::box_score::BoxScore) -> Vec<u8> {
    let mut ret = Vec::new();
    if box_scores.assist.is_some() {
        ret.push(0);
    }
    if box_scores.blocks.is_some() {
        ret.push(1);
    }
    if box_scores.fouled.is_some() {
        ret.push(2);
    }
    if box_scores.fouler.is_some() {
        ret.push(3);
    }
    if box_scores.steals.is_some() {
        ret.push(4);
    }
    if box_scores.turnovers.is_some() {
        ret.push(5);
    }
    if box_scores.points.is_some() {
        ret.push(6);
    }
    if box_scores.paint_points.is_some() {
        ret.push(7);
    }
    if box_scores.threes.is_some() {
        ret.push(8);
    }
    if box_scores.rebounds.is_some() {
        ret.push(9);
    }
    if box_scores.off_rebounds.is_some() {
        ret.push(10);
    }
    if box_scores.def_rebounds.is_some() {
        ret.push(11);
    }
    ret
}
