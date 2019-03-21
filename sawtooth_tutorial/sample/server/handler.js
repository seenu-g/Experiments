const { TransactionHandler } = require('sawtooth-sdk/processor/handler')
const { InvalidTransaction, InternalError } = require('sawtooth-sdk/processor/exceptions')
const cbor = require('cbor')
const crypto = require('crypto')

const XoState = require('./state');
const XoPayload = require('./payload');

const _hash = (x) =>
    crypto.createHash('sha512').update(x).digest('hex').toLowerCase().substring(0, 64)
const XO_FAMILY = 'xo'
const XO_NAMESPACE = _hash(XO_FAMILY).substring(0, 6)

class XOHandler extends TransactionHandler {
    constructor () {
      super(XO_FAMILY, ['1.0'], [XO_NAMESPACE])
    }
  
    apply (transactionProcessRequest, context) {

        let payload = XoPayload.fromBytes(transactionProcessRequest.payload)
        let xoState = new XoState(context)
        let header = transactionProcessRequest.header
        let player = header.signerPublicKey
        if (payload.action === 'create') {
            return xoState.getGame(payload.name).then((game) => {
            if (game !== undefined) {
                throw new InvalidTransaction('Invalid Action: Game already exists.')
            }
            let createdGame = {
                name: payload.name,
                board: '---------',
                state: 'P1-NEXT',
                player1: '',
                player2: ''
            }
            _display(`Player ${player.toString().substring(0, 6)} created game ${payload.name}`)
            return xoState.setGame(payload.name, createdGame)
            })
        } else if (payload.action === 'take') {
            return xoState.getGame(payload.name).then((game) => {
                try {
                  parseInt(payload.space)
                } catch (err) {
                  throw new InvalidTransaction('Space could not be converted as an integer.')
                }
          
                if (payload.space < 1 || payload.space > 9) {
                  throw new InvalidTransaction('Invalid space ' + payload.space)
                }
          
                if (game === undefined) {
                  throw new InvalidTransaction(
                    'Invalid Action: Take requires an existing game.'
                  )
                }
                if (['P1-WIN', 'P2-WIN', 'TIE'].includes(game.state)) {
                  throw new InvalidTransaction('Invalid Action: Game has ended.')
                }
          
                if (game.player1 === '') {
                  game.player1 = player
                } else if (game.player2 === '') {
                  game.player2 = player
                }
                let boardList = game.board.split('')
          
                if (boardList[payload.space - 1] !== '-') {
                  throw new InvalidTransaction('Invalid Action: Space already taken.')
                }
          
                if (game.state === 'P1-NEXT' && player === game.player1) {
                  boardList[payload.space - 1] = 'X'
                  game.state = 'P2-NEXT'
                } else if (
                  game.state === 'P2-NEXT' &&
                  player === game.player2
                ) {
                  boardList[payload.space - 1] = 'O'
                  game.state = 'P1-NEXT'
                } else {
                  throw new InvalidTransaction(
                    `Not this player's turn: ${player.toString().substring(0, 6)}`
                  )
                }
          
                game.board = boardList.join('')
          
                if (_isWin(game.board, 'X')) {
                  game.state = 'P1-WIN'
                } else if (_isWin(game.board, 'O')) {
                  game.state = 'P2-WIN'
                } else if (game.board.search('-') === -1) {
                  game.state = 'TIE'
                }
          
                let playerString = player.toString().substring(0, 6)
          
                _display(
                  `Player ${playerString} takes space: ${payload.space}\n\n` +
                    _gameToStr(
                      game.board,
                      game.state,
                      game.player1,
                      game.player2,
                      payload.name
                    )
                )
          
                return xoState.setGame(payload.name, game)
              })
          } else if (payload.action === 'delete') {
            return xoState.getGame(payload.name).then((game) => {
                if (game === undefined) {
                    throw new InvalidTransaction(`No game exists with name ${payload.name}: unable to delete`)
                }
                return xoState.deleteGame(payload.name)
            })
        } else {
            throw new InvalidTransaction(`Action must be create or take not ${payload.action}`)
        } 
    }
}
module.exports = XOHandler