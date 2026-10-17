from datetime import datetime, timedelta
import secrets
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.user import User, UserPreference
from app.models.hub import Hub, HubMembership
from app.models.game import Game, GameAccount, AccountVerification
from app.models.ratings import PlatformRating, RatingSnapshot
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import Match, MatchResultEvent, MatchReport, MatchEvidence
from app.models.dispute import Dispute
from app.models.badge import Badge, UserBadge
from app.models.audit import DemoDataset
from app.auth.session import hash_password
from app.ratings.elo import determine_tier
from app.utils.logger import logger

FICTIONAL_PLAYERS = [
    ("desta_k", "Desta Kebede", "Addis Ababa", 1540.0, 18),
    ("selam_t", "Selam Tadesse", "Addis Ababa", 1680.0, 24),
    ("biruk_m", "Biruk Mengistu", "Addis Ababa", 1420.0, 12),
    ("almaz_a", "Almaz Assefa", "Addis Ababa", 1810.0, 31),
    ("dawit_g", "Dawit Getachew", "Hawassa", 1350.0, 9),
    ("tigist_b", "Tigist Bekele", "Hawassa", 1590.0, 21),
    ("yared_h", "Yared Haile", "Addis Ababa", 1720.0, 27),
    ("meron_w", "Meron Worku", "Addis Ababa", 1480.0, 15),
    ("abel_t", "Abel Tesfaye", "Addis Ababa", 1290.0, 7),
    ("eden_f", "Eden Fikre", "Addis Ababa", 1610.0, 20),
    ("kaleb_d", "Kaleb Daniel", "Hawassa", 1450.0, 14),
    ("helen_m", "Helen Michael", "Addis Ababa", 1380.0, 11),
    ("yonas_s", "Yonas Solomon", "Addis Ababa", 1750.0, 29),
    ("betty_g", "Bethlehem Girma", "Addis Ababa", 1520.0, 16),
    ("surafel_a", "Surafel Alemayehu", "Addis Ababa", 1640.0, 22),
    ("rahel_z", "Rahel Zegeye", "Hawassa", 1410.0, 10),
    ("samuel_k", "Samuel Kassahun", "Addis Ababa", 1880.0, 35),
    ("marta_y", "Marta Yohannes", "Addis Ababa", 1320.0, 8),
    ("henok_b", "Henok Berhanu", "Addis Ababa", 1560.0, 17),
    ("tsion_a", "Tsion Abera", "Addis Ababa", 1490.0, 13),
    ("kirubel_t", "Kirubel Tamirat", "Hawassa", 1630.0, 25),
    ("genet_d", "Genet Dagne", "Addis Ababa", 1250.0, 6),
    ("natnael_e", "Natnael Ephrem", "Addis Ababa", 1790.0, 30),
    ("hana_g", "Hana Gebre", "Addis Ababa", 1510.0, 15),
    ("tewodros_m", "Tewodros Mulugeta", "Addis Ababa", 1440.0, 12),
    ("saron_k", "Saron Kassa", "Hawassa", 1370.0, 9),
    ("eyob_w", "Eyob Walelign", "Addis Ababa", 1660.0, 23),
    ("liya_t", "Liya Tefera", "Addis Ababa", 1580.0, 19),
    ("robson_d", "Robel Desta", "Addis Ababa", 1460.0, 13),
    ("frehiwot_b", "Frehiwot Bogale", "Addis Ababa", 1710.0, 26),
    ("amanuel_h", "Amanuel Habte", "Hawassa", 1340.0, 8),
    ("mahlet_s", "Mahlet Seyoum", "Addis Ababa", 1530.0, 16),
    ("bereket_t", "Bereket Teshome", "Addis Ababa", 1830.0, 32),
    ("sosina_a", "Sosina Asrat", "Addis Ababa", 1400.0, 10),
    ("fasil_g", "Fasil Gebremariam", "Addis Ababa", 1650.0, 21),
    ("ruth_m", "Ruth Mekonnen", "Hawassa", 1280.0, 5),
    ("ermias_y", "Ermias Yilma", "Addis Ababa", 1740.0, 28),
    ("leyla_k", "Leyla Kemal", "Addis Ababa", 1570.0, 18),
    ("tariku_d", "Tariku Derese", "Addis Ababa", 1430.0, 11),
    ("meseret_b", "Meseret Balcha", "Addis Ababa", 1690.0, 24),
]

class DemoService:
    @staticmethod
    async def seed_demo_data(db: AsyncSession) -> Dict[str, Any]:
        """
        Deterministically creates demo data isolated with is_demo=True.
        """
        logger.info("Starting demo data seeding...")

        # 1. Hubs
        hubs_data = [
            ("Bole Gaming Hub", "bole-hub", "Addis Ababa", "Addis Ababa flagship esports venue at Bole Medhanialem."),
            ("Arada Community Hub", "arada-hub", "Addis Ababa", "Grassroots gaming cafe at Piazza/Arada."),
            ("Hawassa Lakeside Hub", "hawassa-hub", "Hawassa", "Southern regional competitive center in Hawassa.")
        ]
        created_hubs = []
        for name, slug, city, desc in hubs_data:
            stmt = select(Hub).where(Hub.slug == slug)
            h = (await db.execute(stmt)).scalar_one_or_none()
            if not h:
                h = Hub(name=name, slug=slug, city=city, description=desc, is_demo=True)
                db.add(h)
                await db.flush()
            created_hubs.append(h)

        # 2. Hub Captain and Admin accounts
        captain_user = (await db.execute(select(User).where(User.username == "captain_bole"))).scalar_one_or_none()
        if not captain_user:
            captain_user = User(
                username="captain_bole",
                display_name="Captain Dawit (Bole Hub)",
                email="captain@bole.gamebridge.et",
                password_hash=hash_password("captain123"),
                role="hub_captain",
                city="Addis Ababa",
                public_identifier="et-captain-bole",
                is_demo=True
            )
            db.add(captain_user)
            await db.flush()
            db.add(UserPreference(user_id=captain_user.id, language="am"))
            db.add(HubMembership(user_id=captain_user.id, hub_id=created_hubs[0].id, role="captain"))

        admin_user = (await db.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                username="admin",
                display_name="GameBridge Administrator",
                email="admin@gamebridge.et",
                password_hash=hash_password("admin123"),
                role="super_admin",
                city="Addis Ababa",
                public_identifier="et-admin-main",
                is_demo=True
            )
            db.add(admin_user)
            await db.flush()
            db.add(UserPreference(user_id=admin_user.id, language="en"))

        # 3. 40 Fictional Players
        created_players = []
        for uname, dname, city, elo, matches in FICTIONAL_PLAYERS:
            stmt = select(User).where(User.username == uname)
            p = (await db.execute(stmt)).scalar_one_or_none()
            if not p:
                p = User(
                    username=uname,
                    display_name=dname,
                    city=city,
                    password_hash=hash_password("player123"),
                    role="player",
                    public_identifier=f"et-{uname}",
                    is_demo=True
                )
                db.add(p)
                await db.flush()

                # Preference
                db.add(UserPreference(user_id=p.id, language="am" if "Addis" in city else "en"))

                # Platform Rating
                db.add(PlatformRating(
                    user_id=p.id,
                    game_key="lichess",
                    mode="rapid",
                    elo=elo,
                    matches_played=matches,
                    tier=determine_tier(elo),
                    is_demo=True
                ))

                # Hub membership
                hub_id = created_hubs[2].id if city == "Hawassa" else created_hubs[0].id
                db.add(HubMembership(user_id=p.id, hub_id=hub_id, role="player"))

                # Verified Lichess Account
                g_acc = GameAccount(
                    user_id=p.id,
                    game_key="lichess",
                    external_username=f"et_{uname}",
                    status="verified",
                    bio_code="GB-DEMO",
                    verified_at=datetime.utcnow() - timedelta(days=10),
                    is_demo=True
                )
                db.add(g_acc)
                await db.flush()

                # Rating Snapshot
                db.add(RatingSnapshot(
                    game_account_id=g_acc.id,
                    mode="rapid",
                    rating=elo + 20.0,
                    games_played=matches + 15,
                    provisional=False,
                    recorded_at=datetime.utcnow() - timedelta(days=1)
                ))

            created_players.append(p)

        # 4. Badges awarding
        first_win_badge = (await db.execute(select(Badge).where(Badge.key == "first_win"))).scalar_one_or_none()
        champ_badge = (await db.execute(select(Badge).where(Badge.key == "city_champion"))).scalar_one_or_none()
        streak_badge = (await db.execute(select(Badge).where(Badge.key == "streak_10"))).scalar_one_or_none()

        if first_win_badge and champ_badge and created_players:
            # Award top 5 players first win & champion badges
            for p in created_players[:5]:
                b_stmt = select(UserBadge).where(UserBadge.user_id == p.id, UserBadge.badge_id == first_win_badge.id)
                if not (await db.execute(b_stmt)).scalar_one_or_none():
                    db.add(UserBadge(user_id=p.id, badge_id=first_win_badge.id))
            
            # Winner of completed cup gets city_champion
            top_p = created_players[3]  # Almaz (1810)
            c_stmt = select(UserBadge).where(UserBadge.user_id == top_p.id, UserBadge.badge_id == champ_badge.id)
            if not (await db.execute(c_stmt)).scalar_one_or_none():
                db.add(UserBadge(user_id=top_p.id, badge_id=champ_badge.id))

            # Streak badge for top player
            s_stmt = select(UserBadge).where(UserBadge.user_id == top_p.id, UserBadge.badge_id == streak_badge.id)
            if not (await db.execute(s_stmt)).scalar_one_or_none():
                db.add(UserBadge(user_id=top_p.id, badge_id=streak_badge.id))

        # 5. Finished Tournament: Bole Grassroots Cup #1 (8 participants, 3 rounds, full match bracket)
        t1_slug = "bole-grassroots-cup-1"
        t1 = (await db.execute(select(Tournament).where(Tournament.slug == t1_slug))).scalar_one_or_none()
        if not t1 and len(created_players) >= 8:
            t1 = Tournament(
                name="Bole Grassroots Rapid Cup #1",
                slug=t1_slug,
                description="Completed 8-player knockout cup held at Bole Gaming Hub.",
                game_key="lichess",
                mode="rapid",
                hub_id=created_hubs[0].id,
                city="Addis Ababa",
                status="completed",
                max_participants=8,
                start_time=datetime.utcnow() - timedelta(days=2),
                registration_deadline=datetime.utcnow() - timedelta(days=3),
                created_by_id=captain_user.id,
                is_demo=True
            )
            db.add(t1)
            await db.flush()

            # Add participants
            t1_players = created_players[:8]
            for s_idx, p in enumerate(t1_players, start=1):
                db.add(TournamentParticipant(
                    tournament_id=t1.id,
                    user_id=p.id,
                    seed=s_idx,
                    status="winner" if p.id == t1_players[3].id else "eliminated"
                ))

            # Generate matches: 4 quarterfinals, 2 semifinals, 1 final
            # Quarterfinals (Round 1)
            qf_matches = []
            for i in range(4):
                p1 = t1_players[i]
                p2 = t1_players[7 - i]
                winner = p1 if i in [1, 3] else p2
                m = Match(
                    tournament_id=t1.id,
                    round_number=1,
                    match_number=i + 1,
                    player1_id=p1.id,
                    player2_id=p2.id,
                    winner_id=winner.id,
                    status="completed"
                )
                db.add(m)
                await db.flush()
                qf_matches.append(m)

                # Add append-only MatchResultEvent
                db.add(MatchResultEvent(
                    match_id=m.id,
                    acting_user_id=winner.id,
                    outcome="player1_win" if winner.id == p1.id else "player2_win",
                    winner_id=winner.id,
                    reason="Completed on Lichess."
                ))

            # Semifinals (Round 2)
            sf1 = Match(
                tournament_id=t1.id,
                round_number=2,
                match_number=1,
                player1_id=qf_matches[0].winner_id,
                player2_id=qf_matches[1].winner_id,
                winner_id=qf_matches[1].winner_id,
                status="completed"
            )
            sf2 = Match(
                tournament_id=t1.id,
                round_number=2,
                match_number=2,
                player1_id=qf_matches[2].winner_id,
                player2_id=qf_matches[3].winner_id,
                winner_id=qf_matches[3].winner_id,
                status="completed"
            )
            db.add(sf1)
            db.add(sf2)
            await db.flush()

            # Finals (Round 3)
            final_match = Match(
                tournament_id=t1.id,
                round_number=3,
                match_number=1,
                player1_id=sf1.winner_id,
                player2_id=sf2.winner_id,
                winner_id=t1_players[3].id,  # Almaz won!
                status="completed"
            )
            db.add(final_match)
            await db.flush()

            db.add(MatchResultEvent(
                match_id=final_match.id,
                acting_user_id=t1_players[3].id,
                outcome="player2_win",
                winner_id=t1_players[3].id,
                reason="Lichess Rapid Final 1-0."
            ))

        # 6. Live Tournament: Addis Ababa Weekly Cup #2 (registration open / live)
        t2_slug = "addis-weekly-cup-2"
        t2 = (await db.execute(select(Tournament).where(Tournament.slug == t2_slug))).scalar_one_or_none()
        if not t2 and len(created_players) >= 16:
            t2 = Tournament(
                name="Addis Ababa City Cup #2",
                slug=t2_slug,
                description="Live ongoing city cup open for registrations and live demonstration match.",
                game_key="lichess",
                mode="rapid",
                hub_id=created_hubs[1].id,
                city="Addis Ababa",
                status="registration_open",
                max_participants=16,
                start_time=datetime.utcnow() + timedelta(hours=3),
                registration_deadline=datetime.utcnow() + timedelta(hours=2),
                created_by_id=captain_user.id,
                is_demo=True
            )
            db.add(t2)
            await db.flush()

            # Pre-register 6 players so judges can easily see live bracket or join 7th/8th
            for p in created_players[8:14]:
                db.add(TournamentParticipant(
                    tournament_id=t2.id,
                    user_id=p.id,
                    status="registered"
                ))

        # 7. Prepared, demo-only dispute for the Hub Captain walkthrough
        demo_players = [player for player in created_players if player.is_demo][:2]
        review_slug = "captain-review-demo"
        review_tournament = (await db.execute(
            select(Tournament).where(Tournament.slug == review_slug)
        )).scalar_one_or_none()
        if not review_tournament and len(demo_players) == 2:
            review_tournament = Tournament(
                name="Bole Captain Review Cup",
                slug=review_slug,
                description="Demo-only fixture for the captain dispute walkthrough.",
                game_key="lichess",
                mode="rapid",
                hub_id=created_hubs[0].id,
                city="Addis Ababa",
                status="in_progress",
                max_participants=2,
                start_time=datetime.utcnow() - timedelta(hours=2),
                registration_deadline=datetime.utcnow() - timedelta(hours=3),
                created_by_id=captain_user.id,
                is_demo=True
            )
            db.add(review_tournament)
            await db.flush()
            for seed, player in enumerate(demo_players, start=1):
                db.add(TournamentParticipant(
                    tournament_id=review_tournament.id,
                    user_id=player.id,
                    seed=seed,
                    status="active"
                ))
            review_match = Match(
                tournament_id=review_tournament.id,
                round_number=1,
                match_number=1,
                player1_id=demo_players[0].id,
                player2_id=demo_players[1].id,
                status="disputed"
            )
            db.add(review_match)
            await db.flush()
            db.add_all([
                MatchReport(
                    match_id=review_match.id,
                    reporting_user_id=demo_players[0].id,
                    claimed_winner_id=demo_players[0].id,
                    score_p1=1,
                    score_p2=0,
                    comments="Demo report: player one claims the win."
                ),
                MatchReport(
                    match_id=review_match.id,
                    reporting_user_id=demo_players[1].id,
                    claimed_winner_id=demo_players[1].id,
                    score_p1=0,
                    score_p2=1,
                    comments="Demo report: player two disputes the result."
                ),
                Dispute(
                    match_id=review_match.id,
                    opened_by_id=demo_players[1].id,
                    status="open",
                    reason="Prepared demo dispute: the players submitted conflicting match results."
                )
            ])

        # 8. Sample resolved dispute
        # Create a separate disputed match in finished cup for demonstration
        disputed_m_stmt = select(Match).where(Match.tournament_id == (t1.id if t1 else None)).limit(1)
        demo_match = (await db.execute(disputed_m_stmt)).scalars().first()
        if demo_match:
            # 1 Resolved dispute
            disp_res_stmt = select(Dispute).where(Dispute.match_id == demo_match.id)
            if not (await db.execute(disp_res_stmt)).scalar_one_or_none():
                db.add(Dispute(
                    match_id=demo_match.id,
                    opened_by_id=demo_match.player2_id,
                    status="resolved",
                    reason="Opponent claimed win but disconnected during endgame.",
                    captain_decision="confirm_p1",
                    resolved_by_id=captain_user.id,
                    resolved_at=datetime.utcnow() - timedelta(days=1)
                ))

        # 9. Record DemoDataset marker
        db.add(DemoDataset(name="demo_challenge_gate_v1", description="GameBridge 250 Challenge Demo Dataset"))
        await db.commit()

        logger.info("Demo data seeding completed successfully!")
        return {
            "hubs": len(created_hubs),
            "players": len(created_players),
            "tournaments": 3 if review_tournament else 2
        }

    @staticmethod
    async def safe_demo_wipe(db: AsyncSession) -> Dict[str, Any]:
        """
        Safely wipes ONLY demonstration records (where is_demo=True).
        Protects all real pilot users, real matches, real evidence, and audit logs!
        """
        logger.info("Executing safe demo-data wipe...")

        # Delete in proper foreign key order
        # Tournaments marked is_demo
        demo_tourneys = (await db.execute(select(Tournament.id).where(Tournament.is_demo == True))).scalars().all()
        if demo_tourneys:
            # Delete matches in these tournaments
            demo_matches = (await db.execute(select(Match.id).where(Match.tournament_id.in_(demo_tourneys)))).scalars().all()
            if demo_matches:
                await db.execute(delete(Dispute).where(Dispute.match_id.in_(demo_matches)))
                await db.execute(delete(MatchEvidence).where(MatchEvidence.match_id.in_(demo_matches)))
                await db.execute(delete(MatchReport).where(MatchReport.match_id.in_(demo_matches)))
                await db.execute(delete(MatchResultEvent).where(MatchResultEvent.match_id.in_(demo_matches)))
                await db.execute(delete(Match).where(Match.id.in_(demo_matches)))

            await db.execute(delete(TournamentParticipant).where(TournamentParticipant.tournament_id.in_(demo_tourneys)))
            await db.execute(delete(Tournament).where(Tournament.id.in_(demo_tourneys)))

        # Delete demo users
        demo_users = (await db.execute(select(User.id).where(User.is_demo == True))).scalars().all()
        if demo_users:
            await db.execute(delete(UserBadge).where(UserBadge.user_id.in_(demo_users)))
            await db.execute(delete(PlatformRating).where(PlatformRating.user_id.in_(demo_users)))
            
            demo_accs = (await db.execute(select(GameAccount.id).where(GameAccount.user_id.in_(demo_users)))).scalars().all()
            if demo_accs:
                await db.execute(delete(RatingSnapshot).where(RatingSnapshot.game_account_id.in_(demo_accs)))
                await db.execute(delete(AccountVerification).where(AccountVerification.game_account_id.in_(demo_accs)))
                await db.execute(delete(GameAccount).where(GameAccount.id.in_(demo_accs)))

            await db.execute(delete(HubMembership).where(HubMembership.user_id.in_(demo_users)))
            await db.execute(delete(UserPreference).where(UserPreference.user_id.in_(demo_users)))
            await db.execute(delete(User).where(User.id.in_(demo_users)))

        # Delete demo hubs
        await db.execute(delete(Hub).where(Hub.is_demo == True))
        await db.execute(delete(DemoDataset))

        await db.commit()
        logger.info("Demo data wipe completed. Real pilot records preserved.")
        return {"status": "success", "message": "Demo data wiped safely without affecting real pilot users."}
