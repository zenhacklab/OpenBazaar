/**
* App Module
*
* Main App Module
*/
var dummyapp = angular.module('dummyapp', ['ui.router']);

app.config(['$stateProvider','$urlRouterProvider',
	function($stateProvider, $urlRouterProvider) {
		$urlRouterProvider.otherwise("");

		$stateProvider
			.state('viewStore', {
				url: "",
				view: {
					"main":{
						templateUrl: "store/storepage.html",
						controller: "storepageCntrl"
					},
					"option":{
						templateUrl: "store/storelist.html",
						controller: "storelistCntrl"
					}
				},
				controller:'featuresController',
				title:"OpenBazaar",
				currentroute: "front-page"
			})
			.state('viewList', {
				url: "/list",
				templateUrl: "partials/developer.html",
				controller:'devController',
				title:"OpenBazaar | Developer Info",
				currentroute: "dev-page"
			})
			.state('viewUser', {
				url: "/user",
				templateUrl: "partials/signup.html",
				controller:'signupController',
				title: "OpenBazaar | Sign up",
				currentroute: "signup-page"
			})
			.state('makeAccount', {
				url: "/account",
				templateUrl: "partials/login.html",
				controller:'loginController',
				title: "OpenBazaar | Login",
				currentroute: "login-page"
			});

}]);

// Controllers 

// Front Page Controller
app.controller('featuresController', function($scope){});

// Developer Page Controller
app.controller('devController', function($scope){});

// Developer Page Controller
app.controller('signupController', function($scope){});

// Developer Page Controller
app.controller('loginController', function($scope){});

// Non-working Download Controller (Produces 2 Errors)
app.controller('downloadsController', function($scope,OSdetect) {
