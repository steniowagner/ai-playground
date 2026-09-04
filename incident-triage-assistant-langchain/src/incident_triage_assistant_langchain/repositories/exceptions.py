class RepositoryException(Exception):
    retryable = False


class RepositoryUnavailable(RepositoryException):
    retryable = True


class RepositoryDataError(RepositoryException):
    retryable = False
