use std::fmt::Display;

use crate::{
    action::Action,
    box_score::BoxScore,
    Game, Line,
};
use chrono::{Local, TimeZone, Utc};

pub fn game(game: &Game) -> String {
    log::trace!("game");
    let lines = if game.is_active() {
        log::debug!("game is still in progress");
        log::debug!("{:#?}", game);
        render_active_game(game)
    } else if game.has_ended() {
        log::debug!("game has ended");
        render_complete_game(game)
    } else {
        log::debug!("game starts in the future");
        render_pending_game(game)
    };
    lines.into_iter().map(|l| l.render()).collect()
}

fn render_active_game(game: &Game) -> Vec<Line> {
    let mut ret = Vec::new();
    let time = format!("Q{} {}", game.period.as_number(), game.clock);
    ret.push(Line::small(time));
    ret.push(teams_line(game));
    ret.push(scores_line(game));
    ret
}

pub fn box_score(info: &BoxScore, idx: u8) -> Option<String> {
    let (stat, name) = match idx {
        0 => info.assist.clone().map(|info| (info, "Assists")),
        1 => info.blocks.clone().map(|info| (info, "Blocks")),
        2 => info.fouled.clone().map(|info| (info, "Fouled")),
        3 => info.fouler.clone().map(|info| (info, "Fouler")),
        4 => info.steals.clone().map(|info| (info, "Steals")),
        5 => info.turnovers.clone().map(|info| (info, "Turnovers")),
        6 => info.points.clone().map(|info| (info, "Points")),
        7 => info.paint_points.clone().map(|info| (info, "Paint Pts")),
        8 => info.threes.clone().map(|info| (info, "Threes")),
        9 => info.rebounds.clone().map(|info| (info, "Rebounds(*)")),
        10 => info.off_rebounds.clone().map(|info| (info, "Rebounds(o)")),
        11 => info.def_rebounds.clone().map(|info| (info, "Rebounds(d)")),
        _ => unreachable!(),
    }?;

    Some(Line::medium(format!("{}: {} {}", name, stat.name, stat.value)).render())
}

pub fn action(action: &Action) -> String {
    Line::medium(format!(
        "Q{quarter} {clock} {desc}",
        quarter = action.quarter(),
        clock = action.clock(),
        desc = action.desc(),
    ))
    .render()
}

pub fn render_complete_game(game: &Game) -> Vec<Line> {
    let mut ret = Vec::new();
    let start = Local.from_utc_datetime(&game.start_time.naive_utc());
    let when = format!("{}", start.format("%A"));
    ret.push(Line::small(when));
    ret.push(teams_line(game));
    ret.push(scores_line(game));
    ret
}

pub fn render_pending_game(game: &Game) -> Vec<Line> {
    let mut ret = Vec::new();
    let now = Local.from_utc_datetime(&Utc::now().naive_utc());
    let start = Local.from_utc_datetime(&game.start_time.naive_utc());
    let when = if start.date() < now.date() {
        format!("{}", start.format("%a %l:%M%p"))
    } else {
        format!("{}", start.format("%l:%M%p"))
    };
    ret.push(Line::small(when));
    ret.push(teams_line(game));
    ret.push(record_line(game));
    ret
}

pub fn record_line(game: &Game) -> Line {
    let h_record = format!("W {} L {}", game.home.win, game.home.loss);
    let a_record = format!("W {} L {}", game.away.win, game.away.loss);
    Line::Medium(format!(
        "{h_record} {a_record}",
        h_record = h_record,
        a_record = a_record,
    ))
}

pub fn teams_line(game: &Game) -> Line {
    render_large_three_char_pair(&game.home.tri_code, &game.away.tri_code)
}

pub fn scores_line(game: &Game) -> Line {
    render_large_three_char_pair(&game.home.score, &game.away.score)
}

pub fn render_large_three_char_pair(lhs: &impl Display, rhs: &impl Display) -> Line {
    Line::large(format!(
        "{home:>3} {away:>3}",
        home = lhs,
        away = rhs
    ))
}
