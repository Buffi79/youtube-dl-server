<!doctype html>
<html lang="en">

<head>
  <!-- Required meta tags -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <meta name="Description" content="Web frontend for youtube-dl">

  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO"
    crossorigin="anonymous">
  <link href="youtube-dl/static/style.css" rel="stylesheet">
  <script type="text/javascript" src="youtube-dl/static/logic.js"></script>
  <title>sonos-controller</title>
</head>

<body>
  <div class="container d-flex flex-column text-light text-center">
    <div class="flex-grow-1"></div>
    <div class="jumbotron bg-transparent flex-grow-1">
      <h1 class="display-4">_|_</h1>
      <p class="lead">Enter a video url to play the video to sonos. Url can be to YouTube or <a class="text-info"
          href="https://rg3.github.io/youtube-dl/supportedsites.html">any
          other supported site</a></p>
      <hr class="my-4">
      <div>
        <form action="/youtube-dl" method="POST" name="youdlfrom">
          <div class="input-group">
            % if defined('url'):
            <input name="url" type="url" class="form-control" placeholder="URL" aria-label="URL" aria-describedby="button-submit" autofocus value={{url}}>
            % else:
            <input name="url" type="url" class="form-control" placeholder="URL" aria-label="URL" aria-describedby="button-submit" autofocus>
            % end

            % if defined('speaker'):
            <select class="custom-select" name="speaker" data-selected={{speaker}}>
            % else:
            <select class="custom-select" name="speaker">
            % end
                <option value="Sonos" selected disabled hidden>Sonos</option>
                <option value="Bastelzimmer">Bastelzimmer</option>
                <option value="Elena">Elena</option>
                <option value="Dario">Dario</option>
                <option value="Wohnzimmer">Wohnzimmer</option>                
                <option value="Bad">Bad</option>
                <option value="Küche">Küche</option>
                <option value="Garten">Garten</option>
              </optgroup>    
            </select>
            <div class="input-group-append">
              <button class="btn btn-primary" type="submit">Submit</button>
            </div>
          </div>

        % if defined('status'):
        <div class="ui-widget">
            <div class="ui-state-error ui-corner-all" style="padding: 0.7em;">
                <p><span class="ui-icon ui-icon-alert" style="float: left; margin-right: .3em;"></span>{{status}}</p>
                % if defined('replay'):
                  <button class="btn btn-secondary" type="submit" name="replay-button" value="replay" onclick="return replayButton()">Replay</button>
                % end
            </div>
        </div>
        % end
        </form>
      </div>
    </div>
</div>

  <!-- Optional JavaScript -->
  <!-- jQuery first, then Popper.js, then Bootstrap JS -->
  <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
    crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49"
    crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy"
    crossorigin="anonymous"></script>
</body>

</html>
