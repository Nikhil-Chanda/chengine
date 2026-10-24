# chengine

Making my own chess engine to learn how to make things work. This project is still under development.

## Roadmap

Planned improvements:

- Implement the Universal Chess Interface (UCI) protocol.
- Experiment with NNUE or other neural-network methods.
- Run automated engine-versus-engine matches.

## NOTE

This project is an experimental learning project, not a replacement for any model.

Its playing strength is limited by its basic evaluation function, search implementation, and Python performance. A deeper search does not automatically guarantee stronger play.

The engine currently uses a terminal interface and expects the user to play White. It does not yet provide a graphical board or full UCI protocol support.

## Contributions

Contributions, bug reports, and suggestions are welcome.

When contributing:

- Describe the change or bug.
- Include steps to reproduce issues.
- Test that search leaves the board unchanged.
- Verify that the engine only plays legal moves.
- Document new configuration options and dependencies.