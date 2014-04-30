/**
* App Module
*
* Main App Module
*/
var app = angular.module('app', ['ngRoute']);

app.config(['$routeProvider','$locationProvider',
	function($routeProvider,$locationProvider) {
		$routeProvider
			.when('/',{
				templateUrl:'partials/home.html',
				controller:'mainController',
				title:"OpenBazaar"
			});

		// Use HTML5 History API
		$locationProvider.html5Mode(true);
}]);

app.run(['$location', '$rootScope', function($location, $rootScope) {
    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
        $rootScope.title = current.$$route.title;
    });
}]);

app.controller('mainController', function($scope) {
	$scope.page = {
		title: "OpenBazaar"
	},
	$scope.url = {
		url1: "Hello"
	};
	
});
